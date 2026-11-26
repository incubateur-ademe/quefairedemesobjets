"""Review of the enrich cohortes whose lignes are decided one by one (villes,
codes postaux, SIRET, SIREN, lien de succession): a groupe gathers several
acteurs, a ligne is (acteur, champs)."""

import json

import pytest
from data.models.suggestion import SuggestionAction, SuggestionStatut
from django.contrib.auth.models import User
from qfdmo.models.acteur import RevisionActeur
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

API = "/api/suggestions"
AVALIDER = SuggestionStatut.AVALIDER
ATRAITER = SuggestionStatut.ATRAITER
REJETEE = SuggestionStatut.REJETEE
ACTEURS = ["A1", "A2", "A3"]


@pytest.fixture
def client(client):
    client.force_login(User.objects.create_user(username="admin", is_superuser=True))
    return client


@pytest.fixture
def villes():
    """1 groupe « PARIS → Paris » of 3 acteurs, A3 having a correction."""
    cohorte = SuggestionCohorteFactory(
        identifiant_action="dag_villes",
        type_action=SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
    )
    groupe = SuggestionGroupeFactory(
        suggestion_cohorte=cohorte,
        contexte={"ville actuel(le)": "PARIS", "ville proposé(e)": "Paris"},
    )
    for identifiant in ACTEURS:
        ActeurFactory(
            identifiant_unique=identifiant, nom=f"Nom {identifiant}", ville="PARIS"
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur_id=identifiant,
            champs=["ville"],
            valeurs=["Paris"],
        )
    RevisionActeurFactory(identifiant_unique="A3", ville="PARIS")
    return cohorte, groupe


def key(groupe, identifiant):
    return f"{groupe.id}:{identifiant}:ville"


def get(client, path, **params):
    response = client.get(f"{API}{path}", params)
    return response.status_code, response.json()


def post(client, path, payload):
    response = client.post(
        f"{API}{path}", json.dumps(payload), content_type="application/json"
    )
    return response.status_code, response.json()


def decide(client, groupe, action, *identifiants):
    return post(
        client,
        f"/groupes/{groupe.id}/lignes/decision",
        {"cles": [key(groupe, i) for i in identifiants], "action": action},
    )


def statuts(body):
    return {
        ligne["target"]["identifiant_unique"]: ligne["statut"]
        for ligne in body["lignes"]
    }


@pytest.mark.django_db
class TestSerialization:
    def test_one_ligne_per_acteur(self, client, villes):
        cohorte, groupe = villes
        status, body = get(client, f"/cohortes/{cohorte.id}/groupes", afficher="tout")

        assert status == 200
        (item,) = body["items"]
        assert item["libelle"] == "ville actuel(le) : PARIS · ville proposé(e) : Paris"
        assert item["lignes_total"] == 3
        assert [ligne["key"] for ligne in item["lignes"]] == [
            key(groupe, i) for i in ACTEURS
        ]
        a1, _, a3 = item["lignes"]
        assert a1["target"]["nom"] == "Nom A1"
        assert a1["target"]["admin_urls"]["importe"]
        assert a1["acteur"]["actuel"] == {"ville": "PARIS"}
        assert a1["correction"] == {
            "actuel": None,
            "propose": {"ville": "Paris"},
            "etat": "valeur",
        }
        # The correction of A3 is its own, not the one of the groupe
        assert a3["correction"]["actuel"] == {"ville": "PARIS"}
        assert a1["capacites"]["valider"]
        assert a1["capacites"]["refuser"]
        # Nothing to edit for these cohortes
        assert not a1["capacites"]["corriger_correction"]

    @pytest.mark.parametrize(
        "type_action,champ,identifiant",
        [
            # SIRET proposed from the known SIREN: the SIREN of the acteur
            (SuggestionAction.ENRICH_ACTEURS_SIRET, "siret", "siren"),
            # SIREN proposed from the known SIRET: its SIRET
            (SuggestionAction.ENRICH_ACTEURS_SIREN, "siren", "siret"),
        ],
    )
    def test_identifiants_of_the_acteur(self, client, type_action, champ, identifiant):
        cohorte = SuggestionCohorteFactory(type_action=type_action)
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte)
        ActeurFactory(identifiant_unique="A1", siren="123456789", siret="")
        ActeurFactory(identifiant_unique="A2", siren="", siret="98765432100012")
        # The correction takes precedence over the acteur
        RevisionActeurFactory(
            identifiant_unique="A2", siren="111111111", siret="22222222200022"
        )
        for identifiant_unique in ("A1", "A2"):
            SuggestionUnitaireFactory(
                suggestion_groupe=groupe,
                suggestion_modele="RevisionActeur",
                revision_acteur_id=identifiant_unique,
                champs=[champ],
                valeurs=["0"],
            )

        _, body = get(client, f"/cohortes/{cohorte.id}/groupes", afficher="tout")

        expected = {
            "siren": {"A1": "123456789", "A2": "111111111"},
            "siret": {"A1": "", "A2": "22222222200022"},
        }[identifiant]
        assert {
            ligne["target"]["identifiant_unique"]: ligne["target"]["identifiants"]
            for ligne in body["items"][0]["lignes"]
        } == {
            target: [{"champ": identifiant, "valeur": valeur}]
            for target, valeur in expected.items()
        }

    def test_annuaire_has_the_identifiants_of_the_acteurs(self, client):
        cohorte = SuggestionCohorteFactory(
            type_action=SuggestionAction.ENRICH_ACTEURS_SIRET
        )
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte)
        sirens = {"A1": "123456789", "A2": "123456789", "A3": "987654321"}
        for identifiant_unique, siren in sirens.items():
            ActeurFactory(
                identifiant_unique=identifiant_unique,
                nom=f"Nom {identifiant_unique}",
                siren=siren,
            )
            SuggestionUnitaireFactory(
                suggestion_groupe=groupe,
                suggestion_modele="RevisionActeur",
                revision_acteur_id=identifiant_unique,
                champs=["siret"],
                valeurs=["12345678900012"],
            )

        _, body = get(client, f"/groupes/{groupe.id}")

        # 1 entry per SIREN, with its acteurs
        assert body["annuaire"]["siren"] == [
            {
                "source": "target",
                "label": "Acteurs Nom A1, Nom A2",
                "valeur": "123456789",
                "propose": False,
            },
            {
                "source": "target",
                "label": "Acteur Nom A3",
                "valeur": "987654321",
                "propose": False,
            },
        ]
        # The proposed SIRET stays
        assert [i["valeur"] for i in body["annuaire"]["siret"]] == ["12345678900012"]

    def test_no_identifiant_for_the_villes(self, client, villes):
        cohorte, _ = villes
        _, body = get(client, f"/cohortes/{cohorte.id}/groupes", afficher="tout")

        assert body["items"][0]["lignes"][0]["target"]["identifiants"] == []

    def test_policy(self, client, villes):
        cohorte, _ = villes
        _, body = get(client, f"/cohortes/{cohorte.id}")

        assert body["policy"]["can_reject_line"]
        assert body["policy"]["lignes_by_acteur"]
        # No localisation nor Annuaire Entreprises for the villes
        assert body["policy"]["tabs"] == []

    @pytest.mark.parametrize(
        "type_action,tabs",
        [
            (SuggestionAction.ENRICH_ACTEURS_SIRET, ["annuaire"]),
            (SuggestionAction.ENRICH_ACTEURS_SIREN, ["annuaire"]),
            (SuggestionAction.ENRICH_ACTEURS_CP_TYPO, []),
            (SuggestionAction.ENRICH_ACTEURS_LIEN_SUCCESSION, []),
            (SuggestionAction.ENRICH_ACTEURS_CLOSED, []),
            (SuggestionAction.ENRICH_ACTEURS_RGPD, []),
            (SuggestionAction.SOURCE_MODIFICATION, ["localisation", "annuaire"]),
        ],
    )
    def test_tabs(self, client, type_action, tabs):
        cohorte = SuggestionCohorteFactory(type_action=type_action)
        SuggestionGroupeFactory(suggestion_cohorte=cohorte)
        _, body = get(client, f"/cohortes/{cohorte.id}")

        assert body["policy"]["tabs"] == tabs

    @pytest.mark.parametrize(
        "type_action,colonne_parent",
        [
            (SuggestionAction.ENRICH_ACTEURS_CP_TYPO, False),
            (SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO, False),
            (SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO, True),
            (SuggestionAction.SOURCE_MODIFICATION, True),
        ],
    )
    def test_colonne_parent(self, client, type_action, colonne_parent):
        cohorte = SuggestionCohorteFactory(type_action=type_action)
        SuggestionGroupeFactory(suggestion_cohorte=cohorte)
        _, body = get(client, f"/cohortes/{cohorte.id}")

        assert body["policy"]["colonne_parent"] is colonne_parent

    def test_groupe_detail(self, client, villes):
        _, groupe = villes
        status, body = get(client, f"/groupes/{groupe.id}")

        assert status == 200
        assert len(body["lignes"]) == 3


@pytest.mark.django_db
class TestDecisionsLigneParLigne:
    def test_groupe_stays_to_validate_while_a_ligne_is(self, client, villes):
        _, groupe = villes

        status, body = decide(client, groupe, "reject", "A1")
        assert status == 200
        assert body["statut"] == AVALIDER
        assert statuts(body) == {"A1": REJETEE, "A2": AVALIDER, "A3": AVALIDER}
        assert body["lignes_refusees"] == 1

        _, body = decide(client, groupe, "validate", "A2")
        assert body["statut"] == AVALIDER

        _, body = decide(client, groupe, "validate", "A3")
        # Decided with its last ligne: validated, the refused ligne stays refused
        assert body["statut"] == ATRAITER
        assert statuts(body) == {"A1": REJETEE, "A2": ATRAITER, "A3": ATRAITER}
        assert groupe.suggestion_unitaires.get(revision_acteur_id="A1").statut == (
            REJETEE
        )

    def test_all_lignes_refused_refuse_the_groupe(self, client, villes):
        _, groupe = villes
        _, body = decide(client, groupe, "reject", *ACTEURS)

        assert body["statut"] == REJETEE
        assert body["capacites"]["remettre_a_valider"]

    def test_resubmit_a_refused_ligne_reopens_the_groupe(self, client, villes):
        _, groupe = villes
        decide(client, groupe, "reject", "A1")
        _, body = decide(client, groupe, "validate", "A2", "A3")
        assert body["statut"] == ATRAITER

        line = next(
            ligne for ligne in body["lignes"] if ligne["key"] == key(groupe, "A1")
        )
        assert line["capacites"]["remettre_a_valider"]
        status, body = decide(client, groupe, "resubmit", "A1")

        assert status == 200
        assert body["statut"] == AVALIDER
        assert statuts(body) == {"A1": AVALIDER, "A2": ATRAITER, "A3": ATRAITER}

    def test_validate_groupe_keeps_refused_lignes(self, client, villes):
        _, groupe = villes
        decide(client, groupe, "reject", "A1")

        status, body = post(
            client, f"/groupes/{groupe.id}/decision", {"action": "validate"}
        )

        assert status == 200
        assert body["statut"] == ATRAITER
        assert statuts(body) == {"A1": REJETEE, "A2": ATRAITER, "A3": ATRAITER}

    def test_lignes_designated_by_champs_are_ambiguous(self, client, villes):
        _, groupe = villes
        status, _ = post(
            client,
            f"/groupes/{groupe.id}/lignes/decision",
            {"champs": [["ville"]], "action": "validate"},
        )
        assert status == 422

    def test_refused_ligne_cannot_be_refused_again(self, client, villes):
        _, groupe = villes
        decide(client, groupe, "reject", "A1")

        status, _ = decide(client, groupe, "reject", "A1")
        assert status == 409


@pytest.mark.django_db
class TestLignesView:
    def test_lignes_page_and_stats(self, client, villes):
        cohorte, groupe = villes
        decide(client, groupe, "reject", "A1")

        _, body = get(client, f"/cohortes/{cohorte.id}/lignes", afficher="tout")
        assert [item["key"] for item in body["items"]] == [
            key(groupe, i) for i in ACTEURS
        ]
        _, body = get(client, f"/cohortes/{cohorte.id}/lignes")
        assert body["total"] == 2

        _, body = get(client, f"/cohortes/{cohorte.id}/stats", vue="lignes")
        assert body["compteurs"][AVALIDER] == 2
        assert body["compteurs"][REJETEE] == 1
        assert body["totaux_vues"]["lignes"] == 2
        assert body["tuples"] == [{"champs": ["ville"], "count": 2}]

    def test_filter_on_ligne_statut(self, client, villes):
        cohorte, groupe = villes
        decide(client, groupe, "reject", "A1")
        filtre = json.dumps(
            {
                "op": "and",
                "conditions": [
                    {"field": "ligne.statut", "operator": "eq", "value": REJETEE}
                ],
            }
        )

        _, body = get(
            client, f"/cohortes/{cohorte.id}/lignes", afficher="tout", filtre=filtre
        )
        assert [item["key"] for item in body["items"]] == [key(groupe, "A1")]

    def test_filter_on_current_value_of_the_acteur(self, client, villes):
        cohorte, groupe = villes
        filtre = json.dumps(
            {
                "op": "and",
                "conditions": [
                    {
                        "field": "ligne.valeur_actuelle",
                        "operator": "eq",
                        "value": "paris",
                    }
                ],
            }
        )

        _, body = get(
            client, f"/cohortes/{cohorte.id}/lignes", afficher="tout", filtre=filtre
        )
        assert body["total"] == 3


@pytest.mark.django_db
class TestMassActions:
    def selection(self, groupe, *identifiants):
        return {
            "vue": "lignes",
            "selection": {"mode": "ids", "ids": [key(groupe, i) for i in identifiants]},
        }

    def test_preview_and_reject_lignes(self, client, villes):
        cohorte, groupe = villes
        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions/apercu",
            self.selection(groupe, "A1", "A2"),
        )
        assert status == 200
        assert body["compteurs"]["reject"] == 2
        assert body["compteurs"]["validate"] == 2

        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {**self.selection(groupe, "A1", "A2"), "action": "reject"},
        )
        assert status == 200
        assert body["affected"] == 2
        groupe.refresh_from_db()
        assert groupe.statut == AVALIDER

        post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {**self.selection(groupe, "A3"), "action": "validate"},
        )
        groupe.refresh_from_db()
        assert groupe.statut == ATRAITER

    def test_resubmit_lignes(self, client, villes):
        cohorte, groupe = villes
        decide(client, groupe, "reject", *ACTEURS)

        _, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {**self.selection(groupe, "A2"), "action": "resubmit"},
        )

        assert body["affected"] == 1
        groupe.refresh_from_db()
        assert groupe.statut == AVALIDER

    def test_validate_groupes_keeps_refused_lignes(self, client, villes):
        cohorte, groupe = villes
        decide(client, groupe, "reject", "A1")

        post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "groupes",
                "selection": {"mode": "ids", "ids": [groupe.id]},
                "action": "validate",
            },
        )

        groupe.refresh_from_db()
        assert groupe.statut == ATRAITER
        assert groupe.suggestion_unitaires.get(revision_acteur_id="A1").statut == (
            REJETEE
        )


@pytest.mark.django_db
def test_apply_skips_refused_lignes(client, villes):
    _, groupe = villes
    decide(client, groupe, "reject", "A1")
    decide(client, groupe, "validate", "A2", "A3")
    groupe.refresh_from_db()

    groupe.apply()

    assert not RevisionActeur.objects.filter(pk="A1").exists()
    assert RevisionActeur.objects.get(pk="A2").ville == "Paris"
    assert RevisionActeur.objects.get(pk="A3").ville == "Paris"


@pytest.mark.django_db
def test_apply_after_validating_the_groupe_skips_refused_lignes(client, villes):
    _, groupe = villes
    decide(client, groupe, "reject", "A1")
    post(client, f"/groupes/{groupe.id}/decision", {"action": "validate"})
    groupe.refresh_from_db()
    assert groupe.statut == ATRAITER

    groupe.apply()

    assert not RevisionActeur.objects.filter(pk="A1").exists()
    assert RevisionActeur.objects.get(pk="A2").ville == "Paris"
    assert RevisionActeur.objects.get(pk="A3").ville == "Paris"

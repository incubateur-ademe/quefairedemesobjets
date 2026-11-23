"""Review of the ENRICH cohortes: closed SIRET acteurs, RGPD anonymisation."""

import json

import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionStatut,
)
from django.contrib.auth.models import User
from qfdmo.models.acteur import ActeurStatus
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

API = "/api/suggestions"
CLOSED_CHAMPS_VALEURS = [
    ("statut", ActeurStatus.INACTIF),
    ("siret_is_closed", "True"),
    ("parent_reason", "SIRET fermé"),
]


@pytest.fixture
def client(client):
    client.force_login(User.objects.create_user(username="admin", is_superuser=True))
    return client


@pytest.fixture
def closed():
    """A closed cohorte, with a SOURCE and a CLUSTERING cohorte next to it."""
    acteur = ActeurFactory(identifiant_unique="A1", statut=ActeurStatus.ACTIF)
    parent = RevisionActeurFactory(identifiant_unique="P1", statut=ActeurStatus.ACTIF)
    revision = RevisionActeurFactory(
        identifiant_unique="A1", statut=ActeurStatus.ACTIF, parent=parent
    )
    cohorte = SuggestionCohorteFactory(
        identifiant_action="dag_closed",
        type_action=SuggestionAction.ENRICH_ACTEURS_CLOSED,
    )
    groupe = SuggestionGroupeFactory(
        suggestion_cohorte=cohorte,
        acteur=acteur,
        revision_acteur=revision,
        parent_revision_acteur=parent,
    )
    for champ, valeur in CLOSED_CHAMPS_VALEURS:
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur_id="A1",
            champs=[champ],
            valeurs=[valeur],
        )
    SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            identifiant_action="dag_source",
            type_action=SuggestionAction.SOURCE_MODIFICATION,
        )
    )
    SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            identifiant_action="dag_clustering", type_action=SuggestionAction.CLUSTERING
        )
    )
    return cohorte, groupe


def get(client, path, **params):
    response = client.get(f"{API}{path}", params)
    return response.status_code, response.json()


def actions(body):
    return {item["identifiant_action"] for item in body["items"]}


@pytest.mark.django_db
class TestListClosedCohortes:
    def test_listed_with_source_cohortes(self, client, closed):
        _, body = get(client, "/cohortes")

        assert actions(body) == {"dag_closed", "dag_source"}

    def test_filter_on_type(self, client, closed):
        _, body = get(client, "/cohortes", type_action="ENRICH_ACTEURS_CLOSED")
        assert actions(body) == {"dag_closed"}

        _, body = get(
            client,
            "/cohortes",
            type_action=["SOURCE_AJOUT", "SOURCE_MODIFICATION", "SOURCE_SUPRESSION"],
        )
        assert actions(body) == {"dag_source"}

    def test_type_is_a_filter_choice(self, client, closed):
        _, body = get(client, "/cohortes/filtres")

        (type_action,) = [c for c in body["champs"] if c["key"] == "type_action"]
        assert "ENRICH_ACTEURS_CLOSED" in [c["value"] for c in type_action["choix"]]
        assert "CLUSTERING" not in [c["value"] for c in type_action["choix"]]


@pytest.mark.django_db
class TestReviewClosedCohorte:
    def test_detail_and_policy(self, client, closed):
        cohorte, _ = closed
        status, body = get(client, f"/cohortes/{cohorte.id}")

        assert status == 200
        assert body["policy"]["type_action"] == "ENRICH_ACTEURS_CLOSED"
        assert body["policy"]["editable_models"] == [
            "RevisionActeur",
            "ParentRevisionActeur",
        ]

    def test_lignes_are_editable_but_not_reportable(self, client, closed):
        cohorte, groupe = closed
        status, body = get(client, f"/cohortes/{cohorte.id}/groupes", afficher="tout")

        assert status == 200
        (item,) = body["items"]
        assert item["id"] == groupe.id
        assert item["parent"]["identifiant_unique"] == "P1"
        lignes = {tuple(ligne["champs"]): ligne for ligne in item["lignes"]}
        assert set(lignes) == {(champ,) for champ, _ in CLOSED_CHAMPS_VALEURS}
        statut = lignes[("statut",)]
        assert statut["acteur"]["actuel"] == {"statut": ActeurStatus.ACTIF}
        assert statut["correction"]["propose"] == {"statut": ActeurStatus.INACTIF}
        assert statut["capacites"]["valider"]
        assert statut["capacites"]["corriger_correction"]
        assert statut["capacites"]["corriger_parent"]
        # No suggestion on the Acteur: nothing to report nor to restore
        assert not statut["capacites"]["reporter_correction"]
        assert not statut["capacites"]["restaurer_correction"]

    def test_validate_groupe(self, client, closed):
        _, groupe = closed
        response = client.post(
            f"{API}/groupes/{groupe.id}/decision",
            json.dumps({"action": "validate"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["statut"] == SuggestionStatut.ATRAITER
        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.ATRAITER

    def test_groupe_detail(self, client, closed):
        _, groupe = closed
        status, _ = get(client, f"/groupes/{groupe.id}")
        assert status == 200

    def test_other_types_stay_out(self, client):
        crawl = SuggestionCohorteFactory(type_action=SuggestionAction.CRAWL_URLS)
        SuggestionGroupeFactory(suggestion_cohorte=crawl)

        status, _ = get(client, f"/cohortes/{crawl.id}")
        assert status == 404


ANONYMISE = "ANONYMISE POUR RAISON RGPD"


@pytest.fixture
def rgpd():
    """An acteur with a correction: the anonymisation overwrites both."""
    acteur = ActeurFactory(identifiant_unique="R1", nom="Jean Dupont")
    revision = RevisionActeurFactory(identifiant_unique="R1", nom="Jean Dupont")
    cohorte = SuggestionCohorteFactory(
        identifiant_action="dag_rgpd",
        type_action=SuggestionAction.ENRICH_ACTEURS_RGPD,
    )
    groupe = SuggestionGroupeFactory(
        suggestion_cohorte=cohorte, acteur=acteur, revision_acteur=revision
    )
    for modele, fk in (
        ("Acteur", "acteur_id"),
        ("RevisionActeur", "revision_acteur_id"),
    ):
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele=modele,
            champs=["nom"],
            valeurs=[ANONYMISE],
            **{fk: "R1"},
        )
    return cohorte, groupe


@pytest.mark.django_db
class TestReviewRgpdCohorte:
    def test_listed_and_filtered(self, client, rgpd):
        _, body = get(client, "/cohortes", type_action="ENRICH_ACTEURS_RGPD")
        assert actions(body) == {"dag_rgpd"}

    def test_policy(self, client, rgpd):
        cohorte, _ = rgpd
        status, body = get(client, f"/cohortes/{cohorte.id}")

        assert status == 200
        assert body["policy"]["editable_models"] == ["RevisionActeur"]
        assert not body["policy"]["shows_parent"]
        assert not body["policy"]["can_restore"]

    def test_correction_editable_but_not_restorable(self, client, rgpd):
        cohorte, _ = rgpd
        _, body = get(client, f"/cohortes/{cohorte.id}/groupes", afficher="tout")

        (item,) = body["items"]
        (ligne,) = item["lignes"]
        assert ligne["acteur"]["actuel"] == {"nom": "Jean Dupont"}
        assert ligne["acteur"]["propose"] == {"nom": ANONYMISE}
        assert ligne["correction"]["propose"] == {"nom": ANONYMISE}
        capacites = ligne["capacites"]
        assert capacites["valider"]
        assert capacites["corriger_correction"]
        assert capacites["supprimer_correction"]
        # Restoring the value of the acteur would bring back the personal data
        assert not capacites["restaurer_correction"]
        assert not capacites["corriger_parent"]
        assert item["capacites"]["refuser"]

    def test_edit_correction(self, client, rgpd):
        _, groupe = rgpd
        response = client.put(
            f"{API}/groupes/{groupe.id}/propositions",
            json.dumps(
                {
                    "suggestion_modele": "RevisionActeur",
                    "champs": ["nom"],
                    "valeurs": {"nom": "Ressourcerie du quartier"},
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        (ligne,) = response.json()["lignes"]
        assert ligne["correction"]["propose"] == {"nom": "Ressourcerie du quartier"}
        # The anonymisation of the Acteur is kept
        assert ligne["acteur"]["propose"] == {"nom": ANONYMISE}

    def test_restore_refused(self, client, rgpd):
        _, groupe = rgpd
        response = client.post(
            f"{API}/groupes/{groupe.id}/restaurer",
            json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 409
        assert groupe.suggestion_unitaires.get(
            suggestion_modele="RevisionActeur"
        ).valeurs == [ANONYMISE]

    def test_mass_restore_concerns_nothing(self, client, rgpd):
        cohorte, groupe = rgpd
        response = client.post(
            f"{API}/cohortes/{cohorte.id}/actions/apercu",
            json.dumps(
                {"vue": "groupes", "selection": {"mode": "ids", "ids": [groupe.id]}}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        compteurs = response.json()["compteurs"]
        assert compteurs["restore_correction"] == 0
        assert compteurs["report_correction"] == 1

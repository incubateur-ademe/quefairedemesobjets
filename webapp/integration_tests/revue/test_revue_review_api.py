import json

import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.revue.lignes import ligne_statut
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client

API = "/api/suggestions"


@pytest.fixture
def superuser():
    return User.objects.create_user(username="admin", is_superuser=True)


@pytest.fixture
def client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def seed():
    call_command("seed_revue_suggestions")
    return {
        cohorte.type_action: cohorte
        for cohorte in SuggestionCohorte.objects.filter(
            identifiant_action__startswith="seed_revue_"
        )
    }


@pytest.fixture
def modification(seed):
    return seed[SuggestionAction.SOURCE_MODIFICATION]


def get(client, path, **params):
    response = client.get(f"{API}{path}", params)
    return response.status_code, response.json()


def post(client, path, payload, method="post"):
    response = getattr(client, method)(
        f"{API}{path}", json.dumps(payload), content_type="application/json"
    )
    return response.status_code, response.json()


def cond(field, operator, value=None):
    return {"field": field, "operator": operator, "value": value}


def filtre(*conditions, op="and"):
    return json.dumps({"op": op, "conditions": list(conditions)})


def groupe_ids(client, cohorte, **params):
    _, body = get(
        client,
        f"/cohortes/{cohorte.id}/groupes",
        afficher="tout",
        page_size=200,
        **params,
    )
    return {item["id"] for item in body["items"]}


def expected_lignes(cohorte):
    """Lignes of the cohorte computed in Python: {(groupe_id, champs): statut}."""
    lignes = {}
    for groupe in cohorte.suggestion_groupes.prefetch_related("suggestion_unitaires"):
        by_champs = {}
        for su in groupe.suggestion_unitaires.all():
            by_champs.setdefault(tuple(su.champs), []).append(su)
        for champs, sus in by_champs.items():
            lignes[(groupe.id, champs)] = ligne_statut(groupe.statut, sus)
    return lignes


@pytest.mark.django_db
class TestCohorteDetail:
    def test_policy(self, client, seed):
        status, body = get(client, f"/cohortes/{seed['SOURCE_AJOUT'].id}")

        assert status == 200
        assert body["policy"]["shows_parent"] is False
        assert body["policy"]["editable_models"] == ["RevisionActeur"]
        assert body["policy"]["can_reject_line"] is False
        assert body["total_groupes"] == 20


@pytest.mark.django_db
class TestGroupes:
    def test_default_shows_only_groupes_to_validate(self, client, modification):
        status, body = get(client, f"/cohortes/{modification.id}/groupes")

        assert status == 200
        assert body["page_size"] == 100
        assert (
            body["total"]
            == modification.suggestion_groupes.filter(
                statut=SuggestionStatut.AVALIDER
            ).count()
        )
        assert {item["statut"] for item in body["items"]} == {"AVALIDER"}
        ids = [item["id"] for item in body["items"]]
        assert ids == sorted(ids)

    def test_groupe_content(self, client, modification):
        groupe = modification.suggestion_groupes.filter(
            parent_revision_acteur__isnull=False
        ).first()
        _, body = get(
            client,
            f"/cohortes/{modification.id}/groupes",
            afficher="tout",
            filtre=filtre(cond("groupe.id", "eq", groupe.id)),
        )

        (item,) = body["items"]
        assert item["acteur"]["identifiant_unique"] == groupe.acteur_id
        assert item["acteur"]["admin_urls"]["importe"].startswith(
            "/admin/qfdmo/acteur/"
        )
        assert item["parent"]["identifiant_unique"] == groupe.parent_revision_acteur_id
        assert item["parent"]["nb_enfants"] == 1
        assert item["lignes_total"] == len(item["lignes"])
        ligne = item["lignes"][0]
        assert ligne["acteur"]["actuel"] is not None
        assert ligne["acteur"]["propose"] is not None
        assert ligne["key"].startswith(f"{groupe.id}:")
        assert item["lignes"][1]["parent"]["propose"] is not None

    def test_ajout_identity_comes_from_the_source(self, client, seed):
        ajout = seed[SuggestionAction.SOURCE_AJOUT]
        _, body = get(client, f"/cohortes/{ajout.id}/groupes", page_size=1)

        (item,) = body["items"]
        assert item["is_new"] is True
        assert item["acteur"]["identifiant_unique"].startswith("seed_revue_nouveau_")
        assert item["acteur"]["nom"]
        assert item["parent"] is None
        assert all(ligne["parent"] is None for ligne in item["lignes"])
        assert all(ligne["acteur"]["actuel"] is None for ligne in item["lignes"])
        capacites = {
            tuple(ligne["champs"]): ligne["capacites"] for ligne in item["lignes"]
        }
        assert capacites[("nom",)]["reporter_correction"] is True
        assert capacites[("identifiant_unique",)]["reporter_correction"] is False

    def test_page_size_is_bounded(self, client, modification):
        status, _ = get(client, f"/cohortes/{modification.id}/groupes", page_size=201)
        assert status == 422


@pytest.mark.django_db
class TestReviewFilters:
    def test_metadata(self, client, modification):
        status, body = get(client, f"/cohortes/{modification.id}/revue/filtres")

        assert status == 200
        champs = {champ["key"]: champ for champ in body["champs"]}
        assert champs["ligne.statut"]["famille"] == "ligne"
        assert champs["groupe.statut"]["famille"] == "groupe"
        assert "contexte.source_code" in champs
        assert {"value": "latitude,longitude", "label": "latitude + longitude"} in (
            champs["ligne.champs"]["choix"]
        )

    def test_ligne_statut_in_groupes_view_means_at_least_one_ligne(
        self, client, modification
    ):
        lignes = expected_lignes(modification)
        expected = {
            groupe_id
            for (groupe_id, _), statut in lignes.items()
            if statut == SuggestionStatut.ATRAITER
        }
        assert (
            groupe_ids(
                client,
                modification,
                filtre=filtre(cond("ligne.statut", "eq", "ATRAITER")),
            )
            == expected
        )

    def test_two_ligne_conditions_may_match_two_lignes(self, client, modification):
        lignes = expected_lignes(modification)
        with_nom = {g for (g, champs) in lignes if champs == ("nom",)}
        with_url = {g for (g, champs) in lignes if champs == ("url",)}

        assert (
            groupe_ids(
                client,
                modification,
                filtre=filtre(
                    cond("ligne.champ", "eq", "nom"), cond("ligne.champ", "eq", "url")
                ),
            )
            == with_nom & with_url
        )

    def test_groupe_and_acteur_fields(self, client, modification):
        with_parent = set(
            modification.suggestion_groupes.filter(
                parent_revision_acteur__isnull=False
            ).values_list("id", flat=True)
        )
        assert (
            groupe_ids(
                client, modification, filtre=filtre(cond("groupe.a_parent", "eq", True))
            )
            == with_parent
        )
        besancon = set(
            modification.suggestion_groupes.filter(
                acteur__ville="Besançon"
            ).values_list("id", flat=True)
        )
        assert besancon
        assert (
            groupe_ids(
                client,
                modification,
                filtre=filtre(cond("acteur.ville", "eq", "BESANCON")),
            )
            == besancon
        )

    def test_value_columns(self, client, modification):
        with_parent_proposition = set(
            SuggestionUnitaire.objects.filter(
                suggestion_groupe__suggestion_cohorte=modification,
                suggestion_modele="ParentRevisionActeur",
            ).values_list("suggestion_groupe_id", flat=True)
        )
        assert (
            groupe_ids(
                client,
                modification,
                filtre=filtre(cond("ligne.colonne", "eq", "parent")),
            )
            == with_parent_proposition
        )
        assert groupe_ids(
            client,
            modification,
            filtre=filtre(cond("ligne.valeur_source", "icontains", "EXAMPLE.FR")),
        )

    def test_tuples(self, client, modification):
        lignes = expected_lignes(modification)
        expected = {g for (g, champs) in lignes if champs == ("latitude", "longitude")}

        assert (
            groupe_ids(client, modification, tuples=["latitude,longitude"]) == expected
        )


@pytest.mark.django_db
class TestStats:
    @pytest.mark.parametrize("vue", ["groupes", "lignes"])
    def test_counters_count_the_unit_of_the_view(self, client, modification, vue):
        lignes = expected_lignes(modification)
        status, body = get(client, f"/cohortes/{modification.id}/stats", vue=vue)

        assert status == 200
        if vue == "groupes":
            expected = {
                statut: modification.suggestion_groupes.filter(statut=statut).count()
                for statut in SuggestionStatut.values
            }
        else:
            expected = {
                statut: sum(1 for value in lignes.values() if value == statut)
                for statut in SuggestionStatut.values
            }
        assert body["compteurs"] == expected
        assert sum(body["compteurs"].values()) > (100 if vue == "groupes" else 500)
        assert body["totaux_vues"]["lignes"] == sum(
            1 for value in lignes.values() if value == SuggestionStatut.AVALIDER
        )
        tuples = {tuple(t["champs"]): t["count"] for t in body["tuples"]}
        assert ("latitude", "longitude") in tuples


@pytest.fixture
def groupe(superuser):
    """A SOURCE_MODIFICATION groupe of the seed with a correction and a parent."""
    call_command("seed_revue_suggestions")
    groupe = SuggestionGroupe.objects.filter(
        suggestion_cohorte__type_action=SuggestionAction.SOURCE_MODIFICATION,
        parent_revision_acteur__isnull=False,
    ).first()
    SuggestionGroupe.objects.filter(id=groupe.id).update(
        statut=SuggestionStatut.AVALIDER
    )
    groupe.suggestion_unitaires.update(statut=SuggestionStatut.AVALIDER)
    groupe.refresh_from_db()
    return groupe


def champs_of(groupe):
    return sorted({tuple(su.champs) for su in groupe.suggestion_unitaires.all()})


@pytest.mark.django_db
class TestDecisions:
    def test_validating_every_ligne_validates_the_groupe(
        self, client, groupe, superuser
    ):
        lignes = champs_of(groupe)
        for champs in lignes[:-1]:
            status, body = post(
                client,
                f"/groupes/{groupe.id}/lignes/decision",
                {"champs": [list(champs)], "action": "validate"},
            )
            assert status == 200
            assert body["statut"] == "AVALIDER"
        status, body = post(
            client,
            f"/groupes/{groupe.id}/lignes/decision",
            {"champs": [list(lignes[-1])], "action": "validate"},
        )

        assert body["statut"] == "ATRAITER"
        assert body["lignes_validees"] == len(lignes)
        groupe.refresh_from_db()
        assert groupe.decision_par == superuser
        assert groupe.suggestion_cohorte.statut != "SUCCES"

    def test_resubmit_a_ligne_of_a_validated_groupe(self, client, groupe):
        post(client, f"/groupes/{groupe.id}/decision", {"action": "validate"})
        champs = list(champs_of(groupe)[0])

        status, body = post(
            client,
            f"/groupes/{groupe.id}/lignes/decision",
            {"champs": [champs], "action": "resubmit"},
        )

        assert status == 200
        assert body["statut"] == "AVALIDER"
        statuts = {tuple(ligne["champs"]): ligne["statut"] for ligne in body["lignes"]}
        assert statuts.pop(tuple(champs)) == "AVALIDER"
        assert set(statuts.values()) == {"ATRAITER"}
        assert body["decision_par"] is None

    def test_resubmit_a_ligne_of_a_rejected_groupe_reopens_it(self, client, groupe):
        status, body = post(
            client, f"/groupes/{groupe.id}/decision", {"action": "reject"}
        )
        assert body["statut"] == "REJETEE"
        assert body["lignes"][0]["capacites"]["remettre_groupe_a_valider"] is True

        status, body = post(
            client,
            f"/groupes/{groupe.id}/lignes/decision",
            {"champs": [body["lignes"][0]["champs"]], "action": "resubmit"},
        )

        assert body["statut"] == "AVALIDER"
        assert {ligne["statut"] for ligne in body["lignes"]} == {"AVALIDER"}

    def test_conflict(self, client, groupe):
        _, body = post(client, f"/groupes/{groupe.id}/decision", {"action": "validate"})

        status, error = post(
            client,
            f"/groupes/{groupe.id}/decision",
            {"action": "reject", "expected_modifie_le": "2020-01-01T00:00:00Z"},
        )

        assert status == 409
        assert error["code"] == "conflict"
        assert error["current"]["statut"] == "ATRAITER"

    def test_no_refusal_once_validated(self, client, groupe):
        _, body = post(client, f"/groupes/{groupe.id}/decision", {"action": "validate"})

        status, error = post(
            client,
            f"/groupes/{groupe.id}/decision",
            {"action": "reject", "expected_modifie_le": body["modifie_le"]},
        )

        assert status == 409
        assert "refusé" in error["detail"]

    def test_csrf_is_enforced(self, groupe, superuser):
        client = Client(enforce_csrf_checks=True)
        client.force_login(superuser)

        status, _ = post(
            client, f"/groupes/{groupe.id}/decision", {"action": "validate"}
        )

        assert status == 403


@pytest.mark.django_db
class TestCorrections:
    def test_correct_then_delete(self, client, groupe):
        champs = list(champs_of(groupe)[0])
        source = groupe.suggestion_unitaires.get(
            suggestion_modele="Acteur", champs=champs
        )
        valeurs = dict(zip(champs, source.valeurs))
        status, body = post(
            client,
            f"/groupes/{groupe.id}/propositions",
            {
                "suggestion_modele": "ParentRevisionActeur",
                "champs": champs,
                "valeurs": valeurs,
            },
            method="put",
        )

        assert status == 200
        ligne = next(ligne for ligne in body["lignes"] if ligne["champs"] == champs)
        assert ligne["parent"]["propose"] == valeurs
        assert ligne["statut"] == "AVALIDER"
        assert ligne["capacites"]["supprimer_parent"] is True

        query = "&".join(f"champs={champ}" for champ in champs)
        response = client.delete(
            f"{API}/groupes/{groupe.id}/propositions"
            f"?suggestion_modele=ParentRevisionActeur&{query}"
        )

        assert response.status_code == 200
        ligne = next(
            ligne for ligne in response.json()["lignes"] if ligne["champs"] == champs
        )
        assert ligne["parent"]["propose"] is None

    def test_invalid_value_is_refused_on_the_field(self, client, groupe):
        SuggestionUnitaire.objects.get_or_create(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["email"],
            defaults={"valeurs": ["a@example.org"], "acteur_id": groupe.acteur_id},
        )
        status, error = post(
            client,
            f"/groupes/{groupe.id}/propositions",
            {
                "suggestion_modele": "RevisionActeur",
                "champs": ["email"],
                "valeurs": {"email": "pas un email"},
            },
            method="put",
        )

        assert status == 422
        assert error["code"] == "validation"
        assert "email" in error["errors"]

    def test_report_every_ligne_to_the_parent(self, client, groupe):
        status, body = post(client, f"/groupes/{groupe.id}/report", {"cible": "parent"})

        assert status == 200
        for ligne in body["lignes"]:
            assert ligne["parent"]["propose"] == ligne["acteur"]["propose"]
            assert ligne["statut"] == "AVALIDER"
        assert groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur_id=groupe.parent_revision_acteur_id,
        ).count() == len(body["lignes"])

    def test_nothing_to_correct_once_validated(self, client, groupe):
        post(client, f"/groupes/{groupe.id}/decision", {"action": "validate"})

        status, error = post(
            client, f"/groupes/{groupe.id}/report", {"cible": "correction"}
        )

        assert status == 409


@pytest.mark.django_db
class TestGroupeDetail:
    def test_detail_of_a_modification(self, client, modification):
        groupe = modification.suggestion_groupes.filter(
            parent_revision_acteur__isnull=False,
            suggestion_unitaires__champs=["latitude", "longitude"],
        ).first()
        assert groupe, "the seed has a groupe with a parent and a latitude/longitude"
        status, body = get(client, f"/groupes/{groupe.id}")

        assert status == 200
        assert body["id"] == groupe.id
        assert body["lignes"]
        points = {point["key"]: point for point in body["localisation"]["points"]}
        assert set(points) >= {
            "Origin",
            "Acteur",
            "RevisionActeur",
            "ParentRevisionActeur",
        }
        assert points["Origin"]["draggable"] is False
        assert points["Acteur"]["draggable"] is False
        draggable = groupe.statut == SuggestionStatut.AVALIDER
        assert points["RevisionActeur"]["draggable"] is draggable
        assert body["localisation"]["ligne"] == f"{groupe.id}:latitude,longitude"
        assert body["annuaire"]["siren"][-1]["valeur"]

    def test_detail_of_an_ajout(self, client, seed):
        groupe = seed[SuggestionAction.SOURCE_AJOUT].suggestion_groupes.first()
        _, body = get(client, f"/groupes/{groupe.id}")

        assert [point["key"] for point in body["localisation"]["points"]] == ["Acteur"]
        (siret,) = body["annuaire"]["siret"]
        assert siret["source"] == "acteur"
        assert siret["propose"] is True
        assert len(siret["valeur"]) == 14

    def test_not_found(self, client, seed):
        status, body = get(client, "/groupes/0")
        assert status == 404
        assert body["code"] == "not_found"


@pytest.mark.django_db
class TestCreateLocalisationCorrection:
    def test_create_a_correction_without_localisation_ligne(self, client, modification):
        groupe = (
            modification.suggestion_groupes.filter(
                statut=SuggestionStatut.AVALIDER, revision_acteur__isnull=True
            )
            .exclude(suggestion_unitaires__champs=["latitude", "longitude"])
            .first()
        )
        _, body = get(client, f"/groupes/{groupe.id}")
        assert body["localisation"]["creer_correction"] is True
        assert "RevisionActeur" not in [
            p["key"] for p in body["localisation"]["points"]
        ]

        status, body = post(
            client,
            f"/groupes/{groupe.id}/propositions",
            {
                "suggestion_modele": "RevisionActeur",
                "champs": ["latitude", "longitude"],
                "valeurs": {"latitude": "48.85", "longitude": "2.35"},
            },
            method="put",
        )

        assert status == 200
        ligne = next(
            ligne
            for ligne in body["lignes"]
            if ligne["champs"] == ["latitude", "longitude"]
        )
        assert ligne["correction"]["propose"] == {
            "latitude": "48.85",
            "longitude": "2.35",
        }
        assert ligne["acteur"]["propose"] is None
        _, body = get(client, f"/groupes/{groupe.id}")
        assert body["localisation"]["creer_correction"] is False
        correction = next(
            p for p in body["localisation"]["points"] if p["key"] == "RevisionActeur"
        )
        assert correction == {
            "key": "RevisionActeur",
            "latitude": 48.85,
            "longitude": 2.35,
            "draggable": True,
        }

    def test_no_creation_once_decided(self, client, modification):
        groupe = modification.suggestion_groupes.filter(
            statut=SuggestionStatut.ATRAITER, revision_acteur__isnull=True
        ).first()
        _, body = get(client, f"/groupes/{groupe.id}")
        assert body["localisation"]["creer_correction"] is False

        status, _ = post(
            client,
            f"/groupes/{groupe.id}/propositions",
            {
                "suggestion_modele": "RevisionActeur",
                "champs": ["latitude", "longitude"],
                "valeurs": {"latitude": "48.85", "longitude": "2.35"},
            },
            method="put",
        )
        assert status in (404, 409)


@pytest.mark.django_db
def test_add_a_localisation_correction_to_an_existing_correction(client, modification):
    """The acteur has a RevisionActeur, but no proposed localisation on it."""
    groupe = (
        modification.suggestion_groupes.filter(
            statut=SuggestionStatut.AVALIDER, revision_acteur__isnull=False
        )
        .exclude(
            suggestion_unitaires__suggestion_modele="RevisionActeur",
            suggestion_unitaires__champs=["latitude", "longitude"],
        )
        .first()
    )
    _, body = get(client, f"/groupes/{groupe.id}")
    points = {p["key"]: p for p in body["localisation"]["points"]}
    assert "RevisionActeur" in points  # current localisation of the correction
    assert body["localisation"]["creer_correction"] is True

    status, _ = post(
        client,
        f"/groupes/{groupe.id}/propositions",
        {
            "suggestion_modele": "RevisionActeur",
            "champs": ["latitude", "longitude"],
            "valeurs": {
                "latitude": str(points["RevisionActeur"]["latitude"] + 0.001),
                "longitude": str(points["RevisionActeur"]["longitude"]),
            },
        },
        method="put",
    )

    assert status == 200
    assert groupe.suggestion_unitaires.filter(
        suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
    ).exists()
    _, body = get(client, f"/groupes/{groupe.id}")
    assert body["localisation"]["creer_correction"] is False


@pytest.mark.django_db
class TestLignes:
    def test_page_of_lignes_with_their_groupes(self, client, modification):
        lignes = expected_lignes(modification)
        status, body = get(
            client,
            f"/cohortes/{modification.id}/lignes",
            afficher="tout",
            page_size=1000,
        )

        assert status == 200
        assert body["total"] == len(lignes) > 500
        assert body["page_size"] == 1000
        keys = [item["key"] for item in body["items"]]
        assert len(keys) == len(set(keys)) == len(lignes)
        groupes = {groupe["id"]: groupe for groupe in body["groupes"]}
        first = body["items"][0]
        assert first["key"] in {
            ligne["key"] for ligne in groupes[first["groupe_id"]]["lignes"]
        }
        # Ordered by groupe, then as the admin orders the champs
        groupe_ids = [item["groupe_id"] for item in body["items"]]
        assert groupe_ids == sorted(groupe_ids)

    def test_default_shows_lignes_to_validate(self, client, modification):
        lignes = expected_lignes(modification)
        _, body = get(client, f"/cohortes/{modification.id}/lignes", page_size=1000)

        expected = sum(1 for statut in lignes.values() if statut == "AVALIDER")
        assert body["total"] == expected
        statuts = {
            ligne["key"]: ligne["statut"]
            for groupe in body["groupes"]
            for ligne in groupe["lignes"]
        }
        assert {statuts[item["key"]] for item in body["items"]} == {"AVALIDER"}

    def test_groupe_condition_applies_to_the_groupe_of_the_ligne(
        self, client, modification
    ):
        _, body = get(
            client,
            f"/cohortes/{modification.id}/lignes",
            afficher="tout",
            page_size=1000,
            filtre=filtre(cond("groupe.a_parent", "eq", True)),
        )
        with_parent = set(
            modification.suggestion_groupes.filter(
                parent_revision_acteur__isnull=False
            ).values_list("id", flat=True)
        )
        assert {item["groupe_id"] for item in body["items"]} == with_parent

    def test_pagination(self, client, modification):
        _, page1 = get(client, f"/cohortes/{modification.id}/lignes", page_size=100)
        _, page2 = get(
            client, f"/cohortes/{modification.id}/lignes", page_size=100, page=2
        )

        assert len(page1["items"]) == 100
        assert not {i["key"] for i in page1["items"]} & {
            i["key"] for i in page2["items"]
        }

    def test_page_size_is_bounded(self, client, modification):
        status, _ = get(client, f"/cohortes/{modification.id}/lignes", page_size=1001)
        assert status == 422


@pytest.mark.django_db
class TestValeurActuelleFilter:
    def test_current_value_of_the_acteur(self, client, modification):
        groupe = modification.suggestion_groupes.filter(
            suggestion_unitaires__champs=["ville"]
        ).first()
        ville = groupe.acteur.ville  # « Besançon », « Saint-Étienne »…
        expected = {
            g
            for (g, champs) in expected_lignes(modification)
            if champs == ("ville",)
            and SuggestionGroupe.objects.get(id=g).acteur.ville == ville
        }

        _, body = get(
            client,
            f"/cohortes/{modification.id}/lignes",
            afficher="tout",
            page_size=1000,
            filtre=filtre(
                cond("ligne.valeur_actuelle", "eq", ville.upper()),
                cond("ligne.champ", "eq", "ville"),
            ),
        )

        assert {item["groupe_id"] for item in body["items"]} == expected

    def test_contains_and_groupes_view(self, client, modification):
        assert groupe_ids(
            client,
            modification,
            filtre=filtre(cond("ligne.valeur_actuelle", "icontains", "boulevard")),
        ) == set(
            modification.suggestion_groupes.filter(
                acteur__adresse__icontains="boulevard",
                suggestion_unitaires__champs=["adresse"],
            ).values_list("id", flat=True)
        )

    def test_wildcards_are_escaped(self, client, modification):
        assert not groupe_ids(
            client,
            modification,
            filtre=filtre(cond("ligne.valeur_actuelle", "icontains", "%")),
        )

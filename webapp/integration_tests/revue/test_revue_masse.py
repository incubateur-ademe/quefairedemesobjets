import json

import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionUnitaire,
)
from data.revue import masse
from data.revue.lignes import ligne_statut
from django.contrib.auth.models import User
from django.core.management import call_command

API = "/api/suggestions"


@pytest.fixture
def superuser():
    return User.objects.create_user(username="admin", is_superuser=True)


@pytest.fixture
def client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def cohorte():
    call_command("seed_revue_suggestions")
    return SuggestionCohorte.objects.get(
        identifiant_action="seed_revue_modification",
        type_action=SuggestionAction.SOURCE_MODIFICATION,
    )


def post(client, path, payload):
    response = client.post(
        f"{API}{path}", json.dumps(payload), content_type="application/json"
    )
    return response.status_code, response.json()


def filtre_selection(**kwargs):
    return {"mode": "filtre", "afficher": "avalider", **kwargs}


def lignes_of(cohorte):
    lignes = {}
    for groupe in cohorte.suggestion_groupes.prefetch_related("suggestion_unitaires"):
        by_champs = {}
        for su in groupe.suggestion_unitaires.all():
            by_champs.setdefault(tuple(su.champs), []).append(su)
        for champs, sus in by_champs.items():
            lignes[f"{groupe.id}:{','.join(champs)}"] = ligne_statut(groupe.statut, sus)
    return lignes


@pytest.mark.django_db
class TestGroupes:
    def test_preview_counts_what_really_changes(self, client, cohorte):
        groupes = cohorte.suggestion_groupes.order_by("id")
        ids = list(groupes.values_list("id", flat=True)[:30])

        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions/apercu",
            {"vue": "groupes", "selection": {"mode": "ids", "ids": ids}},
        )

        assert status == 200
        selected = groupes.filter(id__in=ids)
        assert (
            body["compteurs"]["validate"] == selected.filter(statut="AVALIDER").count()
        )
        assert body["compteurs"]["reject"] == body["compteurs"]["validate"]
        # Decided groupes, and groupes to validate having validated lignes
        assert body["compteurs"]["resubmit"] == len(
            [
                groupe
                for groupe in selected
                if groupe.statut in ("ATRAITER", "REJETEE")
                or (
                    groupe.statut == "AVALIDER"
                    and groupe.suggestion_unitaires.filter(statut="ATRAITER").exists()
                )
            ]
        )
        assert 0 < body["compteurs"]["report_parent"] < body["compteurs"]["validate"]

    def test_validate_everything_matching_the_filter_except_excluded(
        self, client, cohorte
    ):
        a_valider = list(
            cohorte.suggestion_groupes.filter(statut="AVALIDER")
            .order_by("id")
            .values_list("id", flat=True)
        )
        exclus = a_valider[:2]

        _, preview = post(
            client,
            f"/cohortes/{cohorte.id}/actions/apercu",
            {"vue": "groupes", "selection": filtre_selection(exclus=exclus)},
        )
        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "groupes",
                "action": "validate",
                "selection": filtre_selection(exclus=exclus),
            },
        )

        assert status == 200
        assert body == {"affected": len(a_valider) - 2, "skipped": 0}
        assert preview["compteurs"]["validate"] == body["affected"]
        assert set(
            cohorte.suggestion_groupes.filter(statut="AVALIDER").values_list(
                "id", flat=True
            )
        ) == set(exclus)
        assert (
            not SuggestionUnitaire.objects.filter(
                suggestion_groupe_id__in=a_valider[2:]
            )
            .exclude(statut="ATRAITER")
            .exists()
        )
        assert SuggestionGroupe.objects.get(id=a_valider[2]).decision_par.username == (
            "admin"
        )
        cohorte.refresh_from_db()
        assert cohorte.statut == "AVALIDER"

    def test_reject_then_resubmit(self, client, cohorte):
        ids = list(
            cohorte.suggestion_groupes.filter(statut="AVALIDER").values_list(
                "id", flat=True
            )[:5]
        )
        selection = {"mode": "ids", "ids": ids}

        _, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {"vue": "groupes", "action": "reject", "selection": selection},
        )
        assert body["affected"] == 5
        _, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {"vue": "groupes", "action": "resubmit", "selection": selection},
        )
        assert body["affected"] == 5
        assert set(
            SuggestionGroupe.objects.filter(id__in=ids).values_list("statut", flat=True)
        ) == {"AVALIDER"}

    def test_report_to_the_parent(self, client, cohorte):
        groupes = cohorte.suggestion_groupes.filter(
            statut="AVALIDER", parent_revision_acteur__isnull=False
        )
        ids = list(groupes.values_list("id", flat=True))

        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "groupes",
                "action": "report_parent",
                "selection": {"mode": "ids", "ids": ids},
            },
        )

        assert status == 200
        assert body["affected"] == len(ids)
        for groupe in groupes:
            acteur = {
                tuple(su.champs): su.valeurs
                for su in groupe.suggestion_unitaires.filter(
                    suggestion_modele="Acteur", statut="AVALIDER"
                )
            }
            parent = {
                tuple(su.champs): su.valeurs
                for su in groupe.suggestion_unitaires.filter(
                    suggestion_modele="ParentRevisionActeur"
                )
            }
            assert parent == acteur

    def test_large_report_runs_as_a_task(self, client, cohorte, monkeypatch):
        monkeypatch.setattr(masse, "SUGGESTION_TASK_ASYNC_THRESHOLD", 1)

        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "groupes",
                "action": "report_correction",
                "selection": filtre_selection(),
            },
        )

        # The test backend runs the task immediately: the result comes back at once
        assert status == 200
        assert body["affected"] > 1

    def test_unknown_job(self, client, cohorte):
        response = client.get(f"{API}/jobs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


@pytest.mark.django_db
class TestLignes:
    def test_validate_lignes_of_a_tuple(self, client, cohorte):
        before = lignes_of(cohorte)
        selection = filtre_selection(tuples=["telephone"])
        targeted = {
            key
            for key, statut in before.items()
            if key.endswith(":telephone") and statut == "AVALIDER"
        }

        _, preview = post(
            client,
            f"/cohortes/{cohorte.id}/actions/apercu",
            {"vue": "lignes", "selection": selection},
        )
        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {"vue": "lignes", "action": "validate", "selection": selection},
        )

        assert status == 200
        assert body["affected"] == preview["compteurs"]["validate"] == len(targeted)
        after = lignes_of(cohorte)
        assert all(after[key] == "ATRAITER" for key in targeted)
        changed = {key for key in before if before[key] != after[key]}
        assert changed == targeted

    def test_validating_the_last_lignes_validates_the_groupe(self, client, cohorte):
        groupe = cohorte.suggestion_groupes.filter(statut="AVALIDER").first()
        keys = [k for k in lignes_of(cohorte) if k.startswith(f"{groupe.id}:")]

        post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "lignes",
                "action": "validate",
                "selection": {"mode": "ids", "ids": keys},
            },
        )

        groupe.refresh_from_db()
        assert groupe.statut == "ATRAITER"

    def test_resubmit_a_ligne_of_a_refused_groupe_reopens_it(self, client, cohorte):
        groupe = cohorte.suggestion_groupes.filter(statut="REJETEE").first()
        key = next(k for k in lignes_of(cohorte) if k.startswith(f"{groupe.id}:"))

        _, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {
                "vue": "lignes",
                "action": "resubmit",
                "selection": {"mode": "ids", "ids": [key]},
            },
        )

        assert body["affected"] == 1
        groupe.refresh_from_db()
        assert groupe.statut == "AVALIDER"
        assert not groupe.suggestion_unitaires.exclude(statut="AVALIDER").exists()

    def test_no_refusal_of_lignes(self, client, cohorte):
        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {"vue": "lignes", "action": "reject", "selection": filtre_selection()},
        )
        assert status == 422


@pytest.mark.django_db
class TestResubmitPartiallyValidatedGroupes:
    """A groupe to validate whose lignes are (partly) validated may be put back to
    validate as a whole: its validated lignes go back to validate."""

    @pytest.fixture
    def partial(self, cohorte):
        return [
            groupe
            for groupe in cohorte.suggestion_groupes.filter(statut="AVALIDER")
            if groupe.suggestion_unitaires.filter(statut="ATRAITER").exists()
        ]

    def test_capacity_and_unit_resubmit(self, client, cohorte, partial):
        groupe = partial[0]
        response = client.get(f"{API}/groupes/{groupe.id}")
        assert response.json()["capacites"]["remettre_a_valider"] is True

        status, body = post(
            client, f"/groupes/{groupe.id}/decision", {"action": "resubmit"}
        )

        assert status == 200
        assert {ligne["statut"] for ligne in body["lignes"]} == {"AVALIDER"}
        assert not groupe.suggestion_unitaires.exclude(statut="AVALIDER").exists()

    def test_mass_resubmit_of_lignes_validated(self, client, cohorte, partial):
        """« statut de la ligne = Validé » in the Groupes view, then everything."""
        selection = filtre_selection(
            filtre=json.dumps(
                {
                    "op": "and",
                    "conditions": [
                        {"field": "ligne.statut", "operator": "eq", "value": "ATRAITER"}
                    ],
                }
            )
        )
        _, preview = post(
            client,
            f"/cohortes/{cohorte.id}/actions/apercu",
            {"vue": "groupes", "selection": selection},
        )
        assert preview["compteurs"]["resubmit"] == len(partial) > 0

        status, body = post(
            client,
            f"/cohortes/{cohorte.id}/actions",
            {"vue": "groupes", "action": "resubmit", "selection": selection},
        )

        assert status == 200
        assert body["affected"] == len(partial)
        assert not SuggestionUnitaire.objects.filter(
            suggestion_groupe__in=[g.id for g in partial], statut="ATRAITER"
        ).exists()

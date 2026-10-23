import pytest
from data.models.suggestion import SuggestionAction
from data.models.suggestions.cluster import SuggestionGroupeTypeCluster
from data.views import get_context_from_suggestion_groupe
from django.urls import reverse
from qfdmo.models.acteur import ActeurStatus, RevisionActeur
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


def _parent_id_su(suggestion_groupe, identifiant_unique, change_model_name, valeur):
    return SuggestionUnitaireFactory(
        suggestion_groupe=suggestion_groupe,
        suggestion_modele="RevisionActeur",
        acteur_id=identifiant_unique,
        revision_acteur_id=identifiant_unique,
        ordre=2,
        raison=change_model_name,
        parametres={"change_model_name": change_model_name},
        champs=["parent_id"],
        valeurs=[valeur],
    )


@pytest.fixture
def parent():
    return RevisionActeurFactory(
        identifiant_unique="P1", nom="parent", statut=ActeurStatus.ACTIF
    )


@pytest.fixture
def child(parent):
    acteur = ActeurFactory(identifiant_unique="CHILD", nom="enfant")
    RevisionActeurFactory(identifiant_unique="CHILD", parent=parent)
    return acteur


@pytest.fixture
def orphan():
    return ActeurFactory(identifiant_unique="ORPHAN", nom="orphelin")


@pytest.fixture
def suggestion_groupe(parent, child, orphan):
    suggestion_groupe = SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            type_action=SuggestionAction.CLUSTERING,
        ),
        parent_revision_acteur=parent,
        contexte={
            "cluster_id": "c1",
            "parent_id": "P1",
            "exact_match": {"ville": "laval"},
            "cluster_fields_exact": ["ville"],
            "cluster_fields_fuzzy": ["nom"],
            "acteurs": [
                {"identifiant_unique": "P1", "ville": "laval"},
                {"identifiant_unique": "CHILD", "ville": "laval"},
                {"identifiant_unique": "ORPHAN", "ville": "laval"},
            ],
        },
    )
    SuggestionUnitaireFactory(
        suggestion_groupe=suggestion_groupe,
        suggestion_modele="ParentRevisionActeur",
        parent_revision_acteur_id="P1",
        ordre=1,
        parametres={"change_model_name": "acteur_keep_as_parent"},
        champs=["nom"],
        valeurs=["nouveau nom"],
    )
    _parent_id_su(
        suggestion_groupe, "CHILD", "acteur_verify_presence_in_revision", "P1"
    )
    _parent_id_su(suggestion_groupe, "ORPHAN", "acteur_update_parent_id", "P1")
    return suggestion_groupe


@pytest.mark.django_db
class TestSuggestionGroupeTypeCluster:
    def test_context(self, suggestion_groupe):
        context = get_context_from_suggestion_groupe(suggestion_groupe)

        assert context["identifiant_unique"] == "P1"
        assert context["cluster"]["contexte"]["cluster_id"] == "c1"
        table = context["comparison_table"]
        # 1 row per acteur, parent first
        assert len(table.rows) == 3
        assert "P1" in table.rows[0].cells[0].html_content
        # The already child acteur is displayed, with an editable parent_id
        child_row = table.rows[1]
        parent_after = next(
            cell for cell in child_row.cells if cell.column_key == "parent_after"
        )
        assert parent_after.fields[0].editable
        assert parent_after.fields[0].replace_text == "P1"
        assert parent_after.fields[0].identifiant_unique == "CHILD"

        parent_table = context["cluster"]["parent_comparison_table"]
        assert len(parent_table.rows) == 1
        assert parent_table.rows[0].cells[2].fields[0].field_name == "nom"

    def test_apply(self, suggestion_groupe):
        suggestion_groupe.apply()

        assert RevisionActeur.objects.get(pk="P1").nom == "nouveau nom"
        assert RevisionActeur.objects.get(pk="CHILD").parent_id == "P1"
        assert RevisionActeur.objects.get(pk="ORPHAN").parent_id == "P1"

    def test_detach_child(self, suggestion_groupe):
        sg_type = SuggestionGroupeTypeCluster.from_suggestion_groupe(suggestion_groupe)
        errors = sg_type.update_suggestion_unitaire(
            "RevisionActeur", "CHILD", {"parent_id": " "}
        )
        assert errors is None

        suggestion_groupe.apply()

        assert RevisionActeur.objects.get(pk="CHILD").parent_id is None
        assert RevisionActeur.objects.get(pk="ORPHAN").parent_id == "P1"

    def test_update_unknown_parent(self, suggestion_groupe):
        sg_type = SuggestionGroupeTypeCluster.from_suggestion_groupe(suggestion_groupe)
        errors = sg_type.update_suggestion_unitaire(
            "RevisionActeur", "CHILD", {"parent_id": "UNKNOWN"}
        )
        assert errors == {"parent_id": "Parent UNKNOWN inexistant"}

    def test_view(self, admin_client, suggestion_groupe):
        url = reverse("data:suggestion_groupe", args=[suggestion_groupe.id])

        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Données du parent" in response.content.decode()

        response = admin_client.post(
            url,
            {
                "suggestion_modele": "RevisionActeur",
                "identifiant_unique": "CHILD",
                "fields_values": '{"parent_id": ""}',
                "fields_groups": '[["parent_id"]]',
            },
        )
        assert response.status_code == 200
        su = suggestion_groupe.suggestion_unitaires.get(revision_acteur_id="CHILD")
        assert su.valeurs == [""]

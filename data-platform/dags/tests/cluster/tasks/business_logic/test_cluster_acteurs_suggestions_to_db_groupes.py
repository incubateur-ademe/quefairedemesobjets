"""Same clusters as the legacy suggestions test, written as
SuggestionGroupe/SuggestionUnitaire and applied: the DB state must be the same"""

import pytest
import test_cluster_acteurs_suggestions_to_db_and_apply as legacy
from cluster.tasks.business_logic.cluster_acteurs_suggestions.to_db_groupes import (
    cluster_acteurs_suggestions_to_db_groupes,
)

from data.models.suggestion import SuggestionGroupe, SuggestionUnitaire


@pytest.mark.django_db()
class TestClusterActeursSuggestionsToDbGroupes(
    legacy.TestClusterActeursSuggestionsToDb
):
    @pytest.fixture(autouse=True)
    def suggestions_to_db(self, df, id_action, id_execution, suggestions_list):
        cluster_acteurs_suggestions_to_db_groupes(
            df_clusters=df,
            suggestions=suggestions_list,
            identifiant_action=id_action,
            identifiant_execution=id_execution,
            cluster_fields_exact=legacy.CLUSTER_FIELDS_EXACT,
            cluster_fields_fuzzy=legacy.CLUSTER_FIELDS_FUZZY,
        )

    @pytest.fixture
    def suggestions_from_db(self, cohorts):
        return SuggestionGroupe.objects.filter(suggestion_cohorte=cohorts.first())

    @pytest.fixture
    def groupe_by_cluster_id(self, suggestions_from_db):
        return {g.contexte["cluster_id"]: g for g in suggestions_from_db}

    @staticmethod
    def _unitaire(groupe, identifiant_unique) -> SuggestionUnitaire:
        unitaires = [
            su
            for su in groupe.suggestion_unitaires.all()
            if identifiant_unique
            in [su.revision_acteur_id, su.parent_revision_acteur_id]
        ]
        assert len(unitaires) == 1
        return unitaires[0]

    def test_each_suggestion_has_one_change_per_acteur(self, df, suggestions_from_db):
        for groupe in suggestions_from_db:
            cluster = df[df["cluster_id"] == groupe.contexte["cluster_id"]]
            ids = {
                su.revision_acteur_id or su.parent_revision_acteur_id
                for su in groupe.suggestion_unitaires.all()
            }
            assert ids == set(cluster["identifiant_unique"])

    def test_contexte_lists_all_acteurs(self, df, groupe_by_cluster_id):
        # Unlike the legacy context, existing children are listed
        groupe = groupe_by_cluster_id[legacy.C3]
        ids = {acteur["identifiant_unique"] for acteur in groupe.contexte["acteurs"]}
        cluster = df[df["cluster_id"] == legacy.C3]
        assert ids == set(cluster["identifiant_unique"])
        assert groupe.contexte["exact_match"] == {"ville": "laval"}
        assert groupe.contexte["cluster_fields_fuzzy"] == ["adresse"]

    def test_parent_is_groupe_parent(self, groupe_by_cluster_id):
        assert groupe_by_cluster_id[legacy.C1].parent_revision_acteur_id == "c1pcreate"
        assert groupe_by_cluster_id[legacy.C3].parent_revision_acteur_id == "c3pkeep"

    def test_unitaires(self, groupe_by_cluster_id):
        c1 = groupe_by_cluster_id[legacy.C1]
        create = self._unitaire(c1, "c1pcreate")
        assert create.suggestion_modele == "ParentRevisionActeur"
        assert create.parametres == {"change_model_name": "acteur_create_as_parent"}
        assert (create.champs, create.valeurs) == (["nom"], ["new name c1pcreate"])
        assert create.ordre == 1

        point = self._unitaire(c1, "c1orphan1")
        assert point.suggestion_modele == "RevisionActeur"
        assert point.acteur_id == "c1orphan1"
        assert (point.champs, point.valeurs) == (["parent_id"], ["c1pcreate"])
        assert point.ordre == 2

        c3 = groupe_by_cluster_id[legacy.C3]
        # Already child: no-op parent_id with the current parent
        already_child = self._unitaire(c3, "c3child1_pkeep")
        assert already_child.parametres == {
            "change_model_name": "acteur_verify_presence_in_revision"
        }
        assert (already_child.champs, already_child.valeurs) == (
            ["parent_id"],
            ["c3pkeep"],
        )

        delete = self._unitaire(c3, "c3pdelete")
        assert delete.suggestion_modele == "ParentRevisionActeur"
        assert (delete.champs, delete.valeurs) == ([], [])
        assert delete.ordre == 3

    def test_apply_with_detached_child(self, groupe_by_cluster_id):
        from qfdmo.models.acteur import RevisionActeur

        groupe = groupe_by_cluster_id[legacy.C3]
        already_child = self._unitaire(groupe, "c3child1_pkeep")
        already_child.valeurs = [""]
        already_child.save()

        groupe.apply()

        assert RevisionActeur.objects.get(pk="c3child1_pkeep").parent is None
        c3child2_pkeep = RevisionActeur.objects.get(pk="c3child2_pkeep")
        assert c3child2_pkeep.parent.identifiant_unique == "c3pkeep"

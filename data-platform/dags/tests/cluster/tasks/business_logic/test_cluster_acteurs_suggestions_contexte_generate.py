import pandas as pd
import pytest
from cluster.config.constants import COL_PARENT_ID_BEFORE
from cluster.helpers.shorthands.change_model_name import CHANGE_CREATE, CHANGE_NOTHING
from cluster.tasks.business_logic.cluster_acteurs_suggestions.context import (
    suggestion_context_generate,
)

from data.models.change import COL_CHANGE_MODEL_NAME


class TestSuggestionContexteGenerate:

    @pytest.fixture
    def df_cluster(self) -> pd.DataFrame:
        # The first acteur is a new parent for which
        # we set data to None as it's the case in the
        # pipeline, this allows us verifying that parents
        # to be created aren't taking into account in context
        # precisely because they don't exist yet
        nom = "mon acteur"
        adr = "zone touches"
        return pd.DataFrame(
            {
                "cluster_id": ["c1"] * 3,
                "identifiant_unique": ["parent to be created", "b", "c"],
                "code_postal": [None] + ["53000"] * 2,
                "ville": [None] + ["laval"] * 2,
                "nom": [None, f"{nom} 2", f"{nom} 3"],
                "adresse": [None, f"{adr} 2", f"{adr} 3"],
                COL_CHANGE_MODEL_NAME: [CHANGE_CREATE] + [CHANGE_NOTHING] * 2,
                COL_PARENT_ID_BEFORE: [None] * 3,
            }
        )

    @pytest.fixture
    def working(self, df_cluster) -> dict:
        return suggestion_context_generate(
            df_cluster=df_cluster,
            cluster_fields_exact=["code_postal", "ville"],
            cluster_fields_fuzzy=["nom", "adresse"],
        )

    def test_working_structure(self, working, df_cluster):
        assert isinstance(working, dict)
        assert sorted(list(working.keys())) == sorted(
            ["cluster_id", "exact_match", "fuzzy_details"]
        )
        # Parent to be created should not be in fuzzy details
        assert len(working["fuzzy_details"]) == len(df_cluster) - 1

    def test_working_content(self, working):
        assert working["exact_match"]["code_postal"] == "53000"
        assert working["exact_match"]["ville"] == "laval"
        ids = [x["identifiant_unique"] for x in working["fuzzy_details"]]
        # Parent to be created should not be in fuzzy details
        assert ids == ["b", "c"]

    def test_raise_if_not_one_cluster(self):
        df = pd.DataFrame({"cluster_id": ["c1", "c2"]})
        with pytest.raises(ValueError, match="1 cluster at a time"):
            suggestion_context_generate(df, [], [])

    def test_raise_if_not_exact(self):
        data = {
            "identifiant_unique": ["a1", "a2"],
            "cluster_id": ["c1", "c1"],
            "ville": ["A", "B"],
            COL_CHANGE_MODEL_NAME: [CHANGE_NOTHING] * 2,
            COL_PARENT_ID_BEFORE: [None] * 2,
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="pas 1 groupe de valeur non vide"):
            suggestion_context_generate(df, ["ville"], [])

    def test_exclude_existing_children_from_exact_check(self):
        # Added on 2025-02-20 following this issue:
        # IF children have inconsistent data (e.g. missing in revision)
        # then we would be failing exact check whereas we should simply
        # ignore children from contexte because they are just re-attached
        data = {
            "identifiant_unique": ["a1", "a2", "a3"],
            "cluster_id": ["c1", "c1", "c1"],
            "ville": ["A", None, "Another A"],
            COL_CHANGE_MODEL_NAME: [CHANGE_NOTHING] * 3,
            COL_PARENT_ID_BEFORE: [None, "p1", "p1"],
        }
        df = pd.DataFrame(data)
        suggestion_context_generate(df, ["ville"], [])
        pass

import pandas as pd
import pytest
from compute_acteurs.tasks.business_logic.merge_labels import merge_labels


class TestMergeLabels:
    @pytest.mark.parametrize(
        "load_acteur_labels, load_revisionacteur_labels, load_revisionacteur, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
                pd.DataFrame(columns=["displayedacteur_id", "labelqualite_id"]),
            ),
            (
                pd.DataFrame(columns=["id", "acteur_id", "labelqualite_id"]),
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "revisionacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame({"identifiant_unique": ["actor1", "actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "id": [2],
                        "revisionacteur_id": ["actor2"],
                        "labelqualite_id": [1],
                    },
                ),
                pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "labelqualite_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1],
                        "acteur_id": ["actor1"],
                        "labelqualite_id": [1],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "labelqualite_id"]),
                pd.DataFrame({"identifiant_unique": ["actor1"]}),
                pd.DataFrame(columns=["displayedacteur_id", "labelqualite_id"]),
            ),
        ],
    )
    def test_merge_labels(
        self,
        load_acteur_labels,
        load_revisionacteur_labels,
        load_revisionacteur,
        expected,
    ):

        result = merge_labels(
            df_acteur_labels=load_acteur_labels,
            df_revisionacteur_labels=load_revisionacteur_labels,
            df_revisionacteur=load_revisionacteur,
        )
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )

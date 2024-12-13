import pandas as pd
import pytest
from compute_acteurs.tasks.business_logic.merge_acteur_services import (
    merge_acteur_services,
)


class TestMergeActeurServices:
    @pytest.mark.parametrize(
        "load_acteur_acteur_services, load_revisionacteur_acteur_services,"
        " load_revisionacteur, expected",
        [
            (
                pd.DataFrame(columns=["id", "acteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
                pd.DataFrame(columns=["displayedacteur_id", "acteurservice_id"]),
            ),
            (
                pd.DataFrame(columns=["id", "acteur_id", "acteurservice_id"]),
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "revisionacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame({"identifiant_unique": ["actor1", "actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame(columns=["identifiant_unique"]),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1, 2],
                        "acteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 2],
                    },
                ),
                pd.DataFrame(
                    {
                        "id": [2],
                        "revisionacteur_id": ["actor2"],
                        "acteurservice_id": [1],
                    },
                ),
                # pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame({"identifiant_unique": ["actor2"]}),
                pd.DataFrame(
                    {
                        "displayedacteur_id": ["actor1", "actor2"],
                        "acteurservice_id": [1, 1],
                    },
                    dtype=object,
                ),
            ),
            (
                pd.DataFrame(
                    {
                        "id": [1],
                        "acteur_id": ["actor1"],
                        "acteurservice_id": [1],
                    },
                ),
                pd.DataFrame(columns=["id", "revisionacteur_id", "acteurservice_id"]),
                pd.DataFrame({"identifiant_unique": ["actor1"]}),
                pd.DataFrame(columns=["displayedacteur_id", "acteurservice_id"]),
            ),
        ],
    )
    def test_merge_acteur_services(
        self,
        load_acteur_acteur_services,
        load_revisionacteur_acteur_services,
        load_revisionacteur,
        expected,
    ):

        result = merge_acteur_services(
            df_acteur_acteur_services=load_acteur_acteur_services,
            df_revisionacteur_acteur_services=load_revisionacteur_acteur_services,
            df_revisionacteur=load_revisionacteur,
        )
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )

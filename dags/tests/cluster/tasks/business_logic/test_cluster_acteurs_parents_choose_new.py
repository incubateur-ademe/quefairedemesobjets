import pandas as pd
import pytest
from cluster.config.constants import COL_PARENT_ID_BEFORE
from cluster.helpers.shorthands.change_model_name import (
    CHANGE_CREATE,
    CHANGE_DELETE,
    CHANGE_KEEP,
    CHANGE_NOTHING,
    CHANGE_POINT,
)
from cluster.helpers.shorthands.change_reason import (
    REASON_CREATE,
    REASON_DELETE,
    REASON_KEEP_MOST,
    REASON_KEEP_ONLY,
    REASON_NOTHING,
    REASON_POINT,
)
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    cluster_acteurs_one_cluster_parent_changes_mark,
    cluster_acteurs_one_cluster_parent_choose,
    cluster_acteurs_parents_choose_new,
    parent_id_generate,
)

from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
)
from qfdmo.models.acteur import ActeurStatus

COLS_ASSERT = [
    "identifiant_unique",
    "parent_id",
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
]


def test_parent_id_generate():
    uuid1 = parent_id_generate(["a", "b", "c"])
    uuid2 = parent_id_generate(["a", "c", "b"])
    uuid3 = parent_id_generate(["b", "a", "c"])

    assert uuid1 == uuid2 == uuid3, "UUID générés déterministes et ordre-insensibles"


@pytest.fixture(scope="session")
def df_no_parent() -> pd.DataFrame:
    cid0 = "c0_0parent"
    return pd.DataFrame(
        {
            "cluster_id": [cid0, cid0, cid0],
            "identifiant_unique": ["c0_a", "c0_b", "c0_c"],
            "parent_id": [None, None, None],
            "nombre_enfants": [0, 0, 0],
            "est_parent": [False, False, False],
            "statut": [ActeurStatus.ACTIF, ActeurStatus.ACTIF, ActeurStatus.ACTIF],
        }
    )


@pytest.fixture(scope="session")
def df_one_parent() -> pd.DataFrame:
    cid1 = "c1_1parent"
    return pd.DataFrame(
        {
            "cluster_id": [cid1, cid1, cid1],
            "identifiant_unique": ["c1_a", "c1_b", "c1_c"],
            # b est le parent avec 1 enfant (c), a
            # n'a pas de parent et est rattaché au cluster
            "parent_id": [None, None, "c1_b"],
            "nombre_enfants": [0, 1, 0],
            "est_parent": [False, True, False],
            "statut": [ActeurStatus.ACTIF, ActeurStatus.ACTIF, ActeurStatus.ACTIF],
        }
    )


@pytest.fixture(scope="session")
def df_two_parents() -> pd.DataFrame:
    cid2 = "c2_2parents"
    return pd.DataFrame(
        {
            "cluster_id": [cid2, cid2, cid2, cid2, cid2],
            "identifiant_unique": ["c2_a", "c2_b", "c2_c", "c2_d", "c2_e"],
            # a=2 enfants, b=1 enfant
            "parent_id": [None, None, "c2_b", "c2_a", "c2_a"],
            "nombre_enfants": [2, 1, 0, 0, 0],
            "est_parent": [True, True, False, False, False],
            "statut": [
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
            ],
        }
    )


@pytest.fixture(scope="session")
def df_two_parents_one_inactive() -> pd.DataFrame:
    """Fixture avec 2 parents dont un seul est actif"""
    cid3 = "c3_2parents_one_inactive"
    return pd.DataFrame(
        {
            "cluster_id": [cid3, cid3, cid3, cid3, cid3],
            "identifiant_unique": ["c3_a", "c3_b", "c3_c", "c3_d", "c3_e"],
            # a=2 enfants (INACTIF), b=1 enfant (ACTIF)
            "parent_id": [None, None, "c3_b", "c3_a", "c3_a"],
            "nombre_enfants": [2, 1, 0, 0, 0],
            "est_parent": [True, True, False, False, False],
            "statut": [
                ActeurStatus.INACTIF,  # a est inactif mais a plus d'enfants
                ActeurStatus.ACTIF,  # b est actif mais a moins d'enfants
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
            ],
        }
    )


@pytest.fixture(scope="session")
def df_two_parents_both_active() -> pd.DataFrame:
    """Fixture avec 2 parents actifs, on choisit celui avec le plus d'enfants"""
    cid4 = "c4_2parents_both_active"
    return pd.DataFrame(
        {
            "cluster_id": [cid4, cid4, cid4, cid4, cid4, cid4],
            "identifiant_unique": ["c4_a", "c4_b", "c4_c", "c4_d", "c4_e", "c4_f"],
            # a=3 enfants (ACTIF), b=1 enfant (ACTIF)
            "parent_id": [None, None, "c4_b", "c4_a", "c4_a", "c4_a"],
            "nombre_enfants": [3, 1, 0, 0, 0, 0],
            "est_parent": [True, True, False, False, False, False],
            "statut": [
                ActeurStatus.ACTIF,  # a est actif et a plus d'enfants
                ActeurStatus.ACTIF,  # b est actif mais a moins d'enfants
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
            ],
        }
    )


@pytest.fixture(scope="session")
def df_two_parents_both_inactive() -> pd.DataFrame:
    """Fixture avec 2 parents inactifs, on choisit celui avec le plus d'enfants"""
    cid5 = "c5_2parents_both_inactive"
    return pd.DataFrame(
        {
            "cluster_id": [cid5, cid5, cid5, cid5, cid5],
            "identifiant_unique": ["c5_a", "c5_b", "c5_c", "c5_d", "c5_e"],
            # a=2 enfants (INACTIF), b=1 enfant (INACTIF)
            "parent_id": [None, None, "c5_b", "c5_a", "c5_a"],
            "nombre_enfants": [2, 1, 0, 0, 0],
            "est_parent": [True, True, False, False, False],
            "statut": [
                ActeurStatus.INACTIF,  # a est inactif mais a plus d'enfants
                ActeurStatus.INACTIF,  # b est inactif et a moins d'enfants
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
                ActeurStatus.ACTIF,
            ],
        }
    )


@pytest.fixture(scope="session")
def parent_id_new(df_no_parent) -> str:
    return parent_id_generate(df_no_parent["identifiant_unique"].tolist())


class TestClusterACteursOneClusterParentChoose:

    def test_case_one_parent(self, df_one_parent):
        # Cas de figure avec 1 parent existant (b qui a 1 enfant c)
        # et un nouvel enfant rattaché au cluster (a)
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(df_one_parent)
        assert id == "c1_b"
        assert change == CHANGE_KEEP
        assert reason == REASON_KEEP_ONLY

    def test_case_two_parents(self, df_two_parents):
        # Cas de figure avec 2 parents existants:
        # a = 2 enfants = on le garde
        # b = 1 enfant = on le marque pour suppression
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(df_two_parents)
        assert id == "c2_a"
        assert change == CHANGE_KEEP
        assert reason == REASON_KEEP_MOST

    def test_case_no_parent(self, df_no_parent):
        # Cas de figure avec 0 parent
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(df_no_parent)
        assert id == parent_id_generate(df_no_parent["identifiant_unique"].tolist())
        assert change == CHANGE_CREATE
        assert reason == REASON_CREATE

    def test_case_two_parents_both_active(self, df_two_parents_both_active):
        # Cas de figure avec 2 parents actifs:
        # a = 3 enfants (ACTIF) = on le garde parmi les actifs
        # b = 1 enfant (ACTIF) = on le marque pour suppression
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(
            df_two_parents_both_active
        )
        assert id == "c4_a", "On choisit le parent actif avec le plus d'enfants"
        assert change == CHANGE_KEEP
        assert reason == REASON_KEEP_MOST

    def test_case_two_parents_both_inactive(self, df_two_parents_both_inactive):
        # Cas de figure avec 2 parents inactifs:
        # Comme aucun parent n'est actif, on choisit parmi tous les parents
        # a = 2 enfants (INACTIF) = on le garde (car plus d'enfants)
        # b = 1 enfant (INACTIF) = on le marque pour suppression
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(
            df_two_parents_both_inactive
        )
        assert (
            id == "c5_a"
        ), "On choisit le parent avec le plus d'enfants quand aucun n'est actif"
        assert change == CHANGE_KEEP
        assert reason == REASON_KEEP_MOST

    def test_case_two_parents_one_inactive(self, df_two_parents_one_inactive):
        # Cas de figure avec 2 parents dont un seul est actif:
        # a = 2 enfants (INACTIF)
        # b = 1 enfant (ACTIF) = on le garde car c'est le seul actif
        id, change, reason = cluster_acteurs_one_cluster_parent_choose(
            df_two_parents_one_inactive
        )
        assert id == "c3_b", "On choisit le parent actif même s'il a moins d'enfants"
        assert change == CHANGE_KEEP
        assert reason == REASON_KEEP_MOST


class TestClusterActeursOneClusterChangesMark:

    def test_case_no_parent(self, df_no_parent, parent_id_new):
        # Cas de figure avec 0 parent
        df = df_no_parent
        # On doit simuler le fait d'avoir ajouter la ligne
        # correspondant au nouveau parent, qui est effectué
        # automatiquement dans la fonction cluster_acteurs_parents_choose_new
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "cluster_id": "c0_0parent",
                            "identifiant_unique": parent_id_new,
                            "nombre_enfants": 0,
                            "parent_id": None,
                            "statut": ActeurStatus.ACTIF,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        df = cluster_acteurs_one_cluster_parent_changes_mark(
            df, parent_id_new, CHANGE_CREATE, "Nouveau parent"
        )
        assert len(df) == 4, "Pas de ligne ajoutée ou supprimée"
        assert df[COLS_ASSERT].values.tolist() == [
            ["c0_a", parent_id_new, CHANGE_POINT, 2, REASON_POINT],
            ["c0_b", parent_id_new, CHANGE_POINT, 2, REASON_POINT],
            ["c0_c", parent_id_new, CHANGE_POINT, 2, REASON_POINT],
            [parent_id_new, None, CHANGE_CREATE, 1, "Nouveau parent"],
        ]

    def test_case_one_parent(self, df_one_parent):
        # Cas de figure avec 1 parent existant (b qui a 1 enfant c)
        # et un nouvel enfant rattaché au cluster (a)
        df = df_one_parent
        df = cluster_acteurs_one_cluster_parent_changes_mark(
            df_one_cluster=df,
            parent_id="c1_b",
            change_model_name=CHANGE_KEEP,
            parent_change_reason="b est seul",
        )
        assert len(df) == 3, "Pas de ligne ajoutée ou supprimée"
        assert df[COLS_ASSERT].values.tolist() == [
            ["c1_a", "c1_b", CHANGE_POINT, 2, REASON_POINT],
            ["c1_b", None, CHANGE_KEEP, 1, "b est seul"],
            ["c1_c", "c1_b", CHANGE_NOTHING, 2, REASON_NOTHING],
        ]

    def test_case_two_parents(self, df_two_parents):
        # Cas de figure avec 2 parents existants:
        # a = 2 enfants = on le garde
        # b = 1 enfant = on le marque pour suppression
        df = df_two_parents
        df = cluster_acteurs_one_cluster_parent_changes_mark(
            df, "c2_a", CHANGE_KEEP, "a=2 enfants"
        )
        assert len(df) == 5, "Pas de ligne ajoutée ou supprimée"
        assert df[COLS_ASSERT].values.tolist() == [
            ["c2_a", None, CHANGE_KEEP, 1, "a=2 enfants"],
            ["c2_b", None, CHANGE_DELETE, 3, REASON_DELETE],
            ["c2_c", "c2_a", CHANGE_POINT, 2, REASON_POINT],
            ["c2_d", "c2_a", CHANGE_NOTHING, 2, REASON_NOTHING],
            ["c2_e", "c2_a", CHANGE_NOTHING, 2, REASON_NOTHING],
        ]


class TestClusterActeursChooseAllParents:

    @pytest.fixture(scope="session")
    def df_combined(self, df_one_parent, df_two_parents, df_no_parent) -> pd.DataFrame:
        # Création d'un dataframe qui rassemble tous les cas de figures
        df = pd.concat([df_one_parent, df_two_parents, df_no_parent], ignore_index=True)
        # On mélange les lignes pour tester la robustesse de l'algo
        df = df.sample(frac=1).reset_index(drop=True)
        # Pour tester les nan quand on ajoute des enfants
        df["extra_column"] = "extra_value"
        return df

    @pytest.fixture(scope="session")
    def df_working(self, df_combined) -> pd.DataFrame:
        return cluster_acteurs_parents_choose_new(df_combined)

    def test_working_one_entry_added(
        self, df_working, df_one_parent, df_two_parents, df_no_parent
    ):
        # Seule 1 entrée, correspondant au nouveau parent, est ajoutée.
        # Les entrées correspondant aux parents à supprimer sont conservées
        # pour justement les marquer et plus tard les supprimer
        assert (
            len(df_working)
            == len(df_one_parent) + len(df_two_parents) + len(df_no_parent) + 1
        )

    def test_working_overall_changes(self, df_working, parent_id_new, df_combined):
        # Notations raccourcies pour préserver la lisibilité
        c0 = "c0_0parent"
        c1 = "c1_1parent"
        c2 = "c2_2parents"

        # On a bien tous les changements, ordonnés par cluster_id
        # et par ordre de changement
        cols_assert = [
            "cluster_id",
            "identifiant_unique",
            COL_CHANGE_ORDER,
            COL_CHANGE_MODEL_NAME,
            COL_CHANGE_REASON,
        ]
        assert df_working[cols_assert].values.tolist() == [
            # Cluster 0: 0 parent -> 1 créé
            [c0, parent_id_new, 1, CHANGE_CREATE, REASON_CREATE],  # 🟡 créer
            [c0, "c0_a", 2, CHANGE_POINT, REASON_POINT],  # 🔵 pointer
            [c0, "c0_b", 2, CHANGE_POINT, REASON_POINT],  # 🔵 pointer
            [c0, "c0_c", 2, CHANGE_POINT, REASON_POINT],  # 🔵 pointer
            # Cluster 1: 1 parent -> 1 gardé
            [c1, "c1_b", 1, CHANGE_KEEP, REASON_KEEP_ONLY],  # 🟢 garder
            [c1, "c1_a", 2, CHANGE_POINT, REASON_POINT],  # 🔵 pointer
            [c1, "c1_c", 2, CHANGE_NOTHING, REASON_NOTHING],  # ⚪️ rien à faire
            # Cluster 2: 2 parents -> 1 gardé, 1 supprimé
            [c2, "c2_a", 1, CHANGE_KEEP, REASON_KEEP_MOST],  # 🟢 garder
            [c2, "c2_c", 2, CHANGE_POINT, REASON_POINT],  # 🔵 pointer
            [c2, "c2_d", 2, CHANGE_NOTHING, REASON_NOTHING],  # ⚪️ rien à faire
            [c2, "c2_e", 2, CHANGE_NOTHING, REASON_NOTHING],  # ⚪️ rien à faire
            [c2, "c2_b", 3, CHANGE_DELETE, REASON_DELETE],  # 🔴 supprimer
        ]
        # On veut aucune valeur nan résultant des divers manipulations
        # On ne peut pas juste faire df.isna().any().any() car isna
        # inclut les None qu'on tolère
        df_nan = df_working.map(lambda x: 1 if pd.isna(x) and x is not None else 0)
        assert df_nan.values.sum() == 0

        # On vérifie que la colonne de débug parent_id_before à
        # été ajoutée pour le debug
        assert COL_PARENT_ID_BEFORE in df_working.columns
        # A l'exception du nouveau parent, on confirme qu'elle
        # contient les mêmes valeurs que parent_id de la df d'origine
        df_a = df_working[df_working["identifiant_unique"] != parent_id_new]
        df_a = df_a.sort_values(by="identifiant_unique")
        db_b = df_combined.sort_values(by="identifiant_unique")
        assert df_a[COL_PARENT_ID_BEFORE].tolist() == db_b["parent_id"].tolist()

    def test_pandas_warning(self, df_one_parent, df_two_parents):
        df = pd.concat([df_one_parent, df_two_parents], ignore_index=True)
        df = df[df["cluster_id"] == "c1_1parent"]
        cluster_acteurs_parents_choose_new(df)

"""Un test de bout en bout du clustering, en passant
en dehors d'Airflow pour itérer plus vite.

TODO: quand on est satisfait avec le test: reprendre PR1291
et convertir ce test en test bout-en-bout via Airflow
"""

import re

import pytest
from cluster.tasks.business_logic.cluster_acteurs_clusters import (
    cluster_acteurs_clusters,
)
from cluster.tasks.business_logic.cluster_acteurs_normalize import (
    cluster_acteurs_normalize,
)
from cluster.tasks.business_logic.cluster_acteurs_selection import (
    cluster_acteurs_selection,
)
from rich import print

from dags.cluster.config.model import ClusterConfig
from dags.utils.airflow_params import airflow_params_dropdown_from_mapping
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    SourceFactory,
)

ACTIF = "ACTIF"
INACTIF = "INACTIF"
(
    ID1,
    ID2,
    ID3,
    ID4,
    ID5,
    ID6,
    ID7,
    ID8,
    ID9,
    ID10,
    ID11,
    ID12,
    ID13,
    ID14,
    ID15,
    ID16,
    ID17,
    ID18,
    ID19,
) = [f"id{x}" for x in range(1, 20)]


"""
Légende:
🇪 = acteur enfant (ou si non précisé)
🇵 = acteur parent
"""


@pytest.mark.django_db
class TestClusterActeursE2E:

    @pytest.fixture
    def acteurs_create(self):
        s1 = SourceFactory(code="s1")  # 🟢 inclus
        s2 = SourceFactory(code="s2")  # 🟢 inclus
        s3 = SourceFactory(code="s3")  # 🔴 exclu
        at1 = ActeurTypeFactory(code="at1")  # 🟢 inclus
        at2 = ActeurTypeFactory(code="at2")  # 🟢 inclus
        at3 = ActeurTypeFactory(code="at3")  # 🔴 exclu
        acteurs = [
            # -----------------------------------
            # 🔴 EXCLUS à la sélection
            # -----------------------------------
            # 🇪 source exclue
            (ID1, s3, at1, "s3_at1", "00001", "v1", ACTIF),
            # 🇪 acteur type exclu
            (ID2, s1, at3, "s1_at3", "00001", "v1", ACTIF),
            # 🇪 statut inactif
            (ID3, s1, at1, "s1_at1_inactif", "00001", "v1", INACTIF),
            # 🇪 nom ne match pas le regex
            (ID4, s1, at1, "nom pas bon", "00001", "v1", ACTIF),
            # 🇪 sans code postal (dans include)
            (ID5, s1, at1, "s1 pas de cp", None, "v1", ACTIF),
            # 🇪 sans ville (dans include)
            (ID6, s1, at1, "s1 pas de ville", "00001", None, ACTIF),
            # 🇵: nom ne match pas le regex, ne devrait pas être
            # sur le cluster c5
            (ID7, None, at1, "parent nom pas bon", "00005", "v5", ACTIF),
            # -----------------------------------
            # 🟢 INCLUS à la sélection
            # -----------------------------------
            # 🇪 Cluster taille 1 = 🔴 exclu
            (ID8, s1, at1, "s1_at1_1 tout seul", "00001", "v1", ACTIF),
            # 🇪 Cluster taille 2 mais intra-source = 🔴 exclu
            (ID9, s1, at1, "s1_at1_2a", "00002", "v2", ACTIF),
            (ID10, s1, at1, "s1_at1_2b", "00002", "v2", ACTIF),
            # 🇪 Cluster taille 2 avec 0 parent = 🟢 inclus
            (ID11, s1, at1, "s1 c3 MY âCTEUR a", "00003", "v3", ACTIF),
            (ID12, s2, at1, "s1 c3 mÿ ACTèUR b", "00003", "v3", ACTIF),
            # 🇵+🇪 Cluster taille 3 avec 1 parent = 🟢 inclus
            (ID13, None, at1, "s1 c4 MY âCTEUR p1", "00004", "v4", ACTIF),
            (ID14, s1, at1, "s1 c4 MY äCTéUR a", "00004", "v4", ACTIF),
            (ID15, s2, at1, "s1 c4 MY ACTEûR b", "00004", "v4", ACTIF),
            # 🇵+🇪 Cluster taille 4 avec 2 parent = 🟢 inclus
            # et un mixe d'acteur type
            (ID16, None, at1, "s1 c5 MY âCTEUR p1", "00005", "v5", ACTIF),
            (ID17, None, at2, "s1 c5 MY âCTEUR p2", "00005", "v5", ACTIF),
            (ID18, s1, at1, "s1 c5 MY äCTéUR a", "00005", "v5", ACTIF),
            (ID19, s2, at2, "s1 c5 MY äCTéûR b", "00005", "v5", ACTIF),
        ]
        for acteur in acteurs:
            id, s, at, nom, cp, ville, statut = acteur
            DisplayedActeurFactory(
                identifiant_unique=id,
                source=s,
                acteur_type=at,
                nom=nom,
                code_postal=cp,
                ville=ville,
                statut=statut,
            )
        return s1, s2, s3, at1, at2, at3, acteurs

    def test_e2e(self, acteurs_create):

        s1, s2, s3, at1, at2, at3, acteurs = acteurs_create

        mapping_sources = {x.code: x.id for x in (s1, s2, s3)}
        mapping_acteur_types = {x.code: x.id for x in (at1, at2, at3)}
        dropdown_sources = airflow_params_dropdown_from_mapping(mapping_sources)
        dropdown_atypes = airflow_params_dropdown_from_mapping(mapping_acteur_types)
        include_sources = [x for x in dropdown_sources if re.search("(s1|s2)", x)]
        include_acteur_types = [x for x in dropdown_atypes if re.search("(at1|at2)", x)]
        print(f"{mapping_sources=}")
        print(f"{mapping_acteur_types=}")
        print(f"{dropdown_sources=}")
        print(f"{dropdown_atypes=}")
        print(f"{include_sources=}")
        print(f"{include_acteur_types=}")

        config = ClusterConfig(
            dry_run=False,
            include_sources=include_sources,
            include_acteur_types=include_acteur_types,
            include_only_if_regex_matches_nom=r"s\d",
            include_if_all_fields_filled=["code_postal", "ville"],
            exclude_if_any_field_filled=[],
            # On utilise une regex différente pour les parents
            include_parents_only_if_regex_matches_nom=r"my",
            mapping_sources=mapping_sources,
            mapping_acteur_types=mapping_acteur_types,
            normalize_fields_basic=[],
            normalize_fields_no_words_size1=["nom"],
            normalize_fields_no_words_size2_or_less=[],
            normalize_fields_no_words_size3_or_less=[],
            normalize_fields_order_unique_words=[],
            cluster_intra_source_is_allowed=False,
            cluster_fields_exact=["code_postal", "ville"],
            cluster_fields_fuzzy=["nom"],
            cluster_fuzzy_threshold=0.5,
        )  # type: ignore

        df = cluster_acteurs_selection(
            include_source_ids=config.include_source_ids,
            include_acteur_type_ids=config.include_acteur_type_ids,
            include_only_if_regex_matches_nom=config.include_only_if_regex_matches_nom,
            include_if_all_fields_filled=config.include_if_all_fields_filled,
            exclude_if_any_field_filled=config.exclude_if_any_field_filled,
            include_parents_only_if_regex_matches_nom=config.include_parents_only_if_regex_matches_nom,
            fields_protected=config.fields_protected,
            fields_transformed=config.fields_transformed,
        )

        assert sorted(df["nom"].tolist()) == sorted(
            [
                "s1_at1_1 tout seul",
                "s1_at1_2a",
                "s1_at1_2b",
                # Cluster c3
                "s1 c3 MY âCTEUR a",
                "s1 c3 mÿ ACTèUR b",
                # Cluster c4
                "s1 c4 MY âCTEUR p1",
                "s1 c4 MY äCTéUR a",
                "s1 c4 MY ACTEûR b",
                # Cluster c5
                "s1 c5 MY âCTEUR p1",
                "s1 c5 MY âCTEUR p2",
                "s1 c5 MY äCTéUR a",
                "s1 c5 MY äCTéûR b",
            ]
        )

        df_norm = cluster_acteurs_normalize(
            df,
            normalize_fields_basic=config.normalize_fields_basic,
            normalize_fields_no_words_size1=config.normalize_fields_no_words_size1,
            normalize_fields_no_words_size2_or_less=config.normalize_fields_no_words_size2_or_less,
            normalize_fields_no_words_size3_or_less=config.normalize_fields_no_words_size3_or_less,
            normalize_fields_order_unique_words=config.normalize_fields_order_unique_words,
        )

        print("df_norm")
        print(df_norm.to_dict(orient="records"))

        df_clusters = cluster_acteurs_clusters(
            df_norm,
            cluster_fields_exact=config.cluster_fields_exact,
            cluster_fields_fuzzy=config.cluster_fields_fuzzy,
            cluster_fields_separate=["source_id"],
            cluster_fuzzy_threshold=config.cluster_fuzzy_threshold,
        )

        print("df_clusters")
        print(df_clusters.to_dict(orient="records"))

        assert df_clusters["cluster_id"].nunique() == 3
        assert sorted(
            df_clusters[["cluster_id", "identifiant_unique"]].values.tolist()
        ) == [
            ["00003_v3_nom_1", ID11],
            ["00003_v3_nom_1", ID12],
            ["00004_v4_nom_1", ID13],
            ["00004_v4_nom_1", ID14],
            ["00004_v4_nom_1", ID15],
            ["00005_v5_nom_1", ID16],
            ["00005_v5_nom_1", ID17],
            ["00005_v5_nom_1", ID18],
            ["00005_v5_nom_1", ID19],
        ]

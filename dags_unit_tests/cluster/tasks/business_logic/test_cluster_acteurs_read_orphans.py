import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_read.orphans import (
    cluster_acteurs_read_orphans,
)

from qfdmo.models import RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    RevisionActeurFactory,
    SourceFactory,
)


# Ne pas mettre transaction=True car ceci recréer
# les fixtures DB à chaque test ce qui ralentit
# considérablement les tests pour rien (on fait
# que de la lecture)
@pytest.mark.django_db()
class TestClusterActeursSelectionOrphans:

    @pytest.fixture
    def db_testdata_write(self):
        s1 = SourceFactory(code="s1", libelle="s1")
        s2 = SourceFactory(code="s2", libelle="s2")
        source_pas_bonne = SourceFactory(
            code="source_pas_bonne", libelle="source_pas_bonne"
        )
        at1 = ActeurTypeFactory(code="at1")
        at2 = ActeurTypeFactory(code="at2")
        atype_pas_bon = ActeurTypeFactory(code="atype_pas_bon")

        # ------------------------------------------
        # 🟢 Acteurs qui devraient être inclus
        # 2 acteurs de la source 1 avec mix de type
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="CORRêct_nom_s1_at1",
            adresse="une adresse pas redondante avec le nom",
            ville="Paris",
            code_postal="75000",
        )
        RevisionActeurFactory(
            source=s1,
            acteur_type=at2,
            nom="CORRêct_nom_s1_at2",
            adresse="une adresse pas redondante avec le nom",
            ville="Paris",
            code_postal="75000",
        )
        # 1 acteur de la source 2
        RevisionActeurFactory(
            source=s2,
            acteur_type=at1,
            nom="!!correct_nom_s2_at1",
            ville="Laval",
            code_postal="53000",
        )

        # ------------------------------------------
        # 🟡 Acteurs qui devraient être exclus
        # identique au 1er bon acteur MAIS INACTIF
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="correct_nom_mais_inactif",
            adresse="une adresse pas redondante avec le nom",
            ville="Paris",
            code_postal="75000",
            statut="INACTIF",
        )
        # ville "" alors que champ dans include_if_all_fields_filled
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="correct_nom_mais_ville_vide",
            ville="",
        )
        # siret rempli alors que champ dans exclude_if_any_field_filled
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="nom_correct_mais_siret",
            ville="Paris",
            siret="01234567891234",
        )
        # nom qui ne match pas include_only_if_regex_matches_nom
        RevisionActeurFactory(
            source=s1, acteur_type=at1, nom="nom_match_pas_regex", ville="Paris"
        )
        # source pas dans include_source_ids
        RevisionActeurFactory(
            source=source_pas_bonne,
            acteur_type=at1,
            nom="correct_nom_mais_mauvaise_source",
            ville="Paris",
        )
        # type pas dans include_acteur_type_ids
        RevisionActeurFactory(
            source=s1,
            acteur_type=atype_pas_bon,
            nom="correct_nom_mais_mauvais_type",
            ville="Paris",
        )
        # numero_et_complement_de_rue rempli
        # alors que champ dans exclude_if_any_field_filled
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="correct_nom_mais_numero_rue",
            ville="Paris",
            adresse="1 rue de la paix",
        )
        # adresse redondante avec le nom
        # et nom_sans_combine_adresses dans
        # include_if_all_fields_filled
        RevisionActeurFactory(
            source=s1,
            acteur_type=at1,
            nom="correct nom mais redondant adresse",
            ville="Paris",
            # La fonction de redondance s'attarde sur les mots
            # peut importe l'ordre
            adresse="correct nom redondant mais adresse",
        )

        return s1, s2, at1, at2

    # ----------------------------------------------------
    # Tests sur le cas idéal
    # ----------------------------------------------------
    @pytest.fixture
    def ideal_scenario_apply_function(self, db_testdata_write):
        """La fixture qui construit la df pour le scénario idéal
        et nous permettre de bien scinder les tests après.

        Pour les tests d'échecs qui nécessitent chacun le propre
        df, on fait la construction de la df + tests dans chaque
        test correspondant"""
        s1, s2, at1, at2 = db_testdata_write

        return cluster_acteurs_read_orphans(
            model_class=RevisionActeur,
            include_source_ids=[s1.id, s2.id],
            include_acteur_type_ids=[at1.id, at2.id],
            include_only_if_regex_matches_nom="correct",
            include_if_all_fields_filled=[
                "nom",
                "ville",
                "code_postal",
                "nom_sans_combine_adresses",
            ],
            exclude_if_any_field_filled=["siret", "numero_et_complement_de_rue"],
            extra_dataframe_fields=["longitude", "latitude"],
        )

    @pytest.fixture
    def df_ideal(self, ideal_scenario_apply_function):
        """La dataframe correspondant au cas idéal
        de fonctionnement de la fonction"""
        df = ideal_scenario_apply_function[0]
        # Pour faciliter le debug si besoin, bcp plus simple
        # d'utiliser les dicts que du print df potentiellement
        # tronqué
        # print("contenu df_ideal", df.to_dict(orient="records"))
        return df

    @pytest.fixture
    def query(self, ideal_scenario_apply_function):
        return ideal_scenario_apply_function[1]

    def test_first_argument_is_dataframe(self, df_ideal):
        assert isinstance(df_ideal, pd.DataFrame)

    def test_second_argument_is_query_string(self, query):
        """Récupérer la requête utilisée nous permet de l'afficher
        dans Airflow pour faciliter le debug (on peut copier/coller
        et rejouer la requête si besoin)"""
        assert isinstance(query, str)

    @pytest.mark.parametrize(
        "field",
        [
            "identifiant_unique",
            "statut",
            "source_id",
            "source_code",  # enrichissement débug
            "acteur_type_id",
            "acteur_type_code",  # enrichissement débug
            "nom",
        ],
    )
    def test_df_fields_default_included(self, df_ideal, field):
        """On inclue toujours certains champs par défaut"""
        assert field in df_ideal.columns

    def test_df_field_nom_always_included(self, df_ideal):
        """On ajoute toujours le nom même si il est spécifié dans
        aucun des paramètres (car le métier s'attend à voir le nom
        MAIS il est possible qu'il soit manquant des paramètres du
        fait des comportements par défaut)"""
        assert "nom" in df_ideal.columns

    def test_statut_actif_hard_filter(self, df_ideal):
        """On vérifie que le filtre sur le statut actif est bien appliqué"""
        assert "correct_nom_mais_inactif" not in df_ideal["nom"].values

        # On garde le test en dure "ACTIF" (et non pas répliquer la logique
        # de la fonction) pour éviter de répliquer les erreurs fonctions/tests
        # Ce statut ne devrait pas changer sauf décision métier exceptionnelle
        # donc OK d'avoir du static
        assert all(df_ideal["statut"] == "ACTIF")

    def test_df_properties_requested_included(self, df_ideal):
        """Bien que les propriétés (@property) ne soient pas supportées
        par le QuerySet de Django (elles n'existent pas en base de données), on
        les inclues dans les DataFrame en construisant la df_ideal à partir
        des instances de modèles qui elles on accès à ces propriétés"""
        assert "longitude" in df_ideal.columns
        assert "latitude" in df_ideal.columns

    def test_df_not_all_fields_included(self, df_ideal):
        """On démontre que la df_ideal ne contient que ce qui est nécessaire
        au travaille de clustering (à savoir ce qui à été demandé + quelques
        défaults) MAIS PAS tous les champs"""

        # Bien qu'on ai demandé la longitude et la latitude, on a pas
        # demandé le location
        assert "location" not in df_ideal.columns

    def test_include_source_ids(self, df_ideal):
        """On vérifie que le filtre sur les sources fonctionne"""
        assert "correct_nom_mais_mauvaise_source" not in df_ideal["nom"].values

    def test_include_acteur_type_ids(self, df_ideal):
        """On vérifie que le filtre sur les types d'acteurs fonctionne"""
        assert "correct_nom_mais_mauvais_type" not in df_ideal["nom"].values

    def test_include_only_if_regex_matches_nom(self, df_ideal):
        """On vérifie que le filtre sur le nom fonctionne"""

        # On note qu'une normalisation à la volée est faite
        # sur le nom (ex: CORRêct_nom_s1_at1 -> correct_test_1)
        # ce qui permet l'utilisation de regexs simplifiées
        assert "CORRêct_nom_s1_at1" in df_ideal["nom"].values
        assert "nom_match_pas_regex" not in df_ideal["nom"].values

    def test_include_if_all_fields_filled(self, df_ideal):
        """On n'inclue que les acteurs qui ont tous les champs remplis,
        et par remplis on entend non None et non chaine vide"""
        assert "correct_nom_mais_ville_none" not in df_ideal["nom"].values
        assert "correct_nom_mais_ville_vide" not in df_ideal["nom"].values

        # On démontre que l'inclusion fonctionne également sur les @property
        assert "correct nom mais redondant adresse" not in df_ideal["nom"].values

    def test_exclude_if_any_field_filled(self, df_ideal):
        """On exclue les acteurs qui ont au moins un champ rempli"""
        assert "correct_nom_mais_ville_none" not in df_ideal["nom"].values
        assert "correct_nom_mais_ville_vide" not in df_ideal["nom"].values

        # On démontre que l'exclusion fonctionne également sur les @property
        assert "correct_nom_mais_numero_rue" not in df_ideal["nom"].values

    def test_enrichment_of_source_and_acteur_type_codes(self, df_ideal):
        """On s'assure que les codes des sources et des types d'acteurs
        sont bien inclus dans la dataframe"""
        assert "source_code" in df_ideal.columns
        assert "acteur_type_code" in df_ideal.columns
        assert sorted(df_ideal["source_code"].values.tolist()) == [
            "s1",
            "s1",
            "s2",
        ]
        assert sorted(df_ideal["acteur_type_code"].values.tolist()) == [
            "at1",
            "at1",
            "at2",
        ]

    def test_no_type_inference_from_pandas(self, df_ideal):
        """Les types qui pourraient être inférés par Pandas
        ne le sont pas
        (ex: code_postal: "53000" str -> 53000 int)"""
        assert df_ideal["code_postal"].dtype == "object"
        assert sorted(df_ideal["code_postal"].values.tolist()) == [
            "53000",
            "75000",
            "75000",
        ]

    def test_extra_dataframe_fields(self, df_ideal):
        """On vérifie que les champs supplémentaires demandés sont bien inclus"""
        assert "longitude" in df_ideal.columns
        assert "latitude" in df_ideal.columns

    def test_ideal_scenario_final_results(self, df_ideal):
        """Un petit test pour s'assurer de la cohérence d'ensemble
        des résultats"""
        assert df_ideal.shape[0] == 3
        assert sorted(df_ideal["nom"].values.tolist()) == [
            "!!correct_nom_s2_at1",
            "CORRêct_nom_s1_at1",
            "CORRêct_nom_s1_at2",
        ]

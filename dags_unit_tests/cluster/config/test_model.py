import pytest

from dags.cluster.config.model import ClusterConfig


class TestClusterConfigModel:

    @pytest.fixture
    def params_working(self) -> dict:
        # Paramètres pour créer une config qui fonctionne
        return {
            "dry_run": True,
            "include_sources": ["source1 (id=1)", "source3 (id=3)"],
            "include_acteur_types": ["atype2 (id=2)", "atype3 (id=3)"],
            "include_only_if_regex_matches_nom": "mon nom",
            "include_if_all_fields_filled": ["f1_incl", "f2_incl"],
            "exclude_if_any_field_filled": ["f3_excl", "f4_excl"],
            "include_parents_only_if_regex_matches_nom": None,
            "normalize_fields_basic": ["basic1", "basic2"],
            "normalize_fields_no_words_size1": ["size1"],
            "normalize_fields_no_words_size2_or_less": ["size2"],
            "normalize_fields_no_words_size3_or_less": ["size3"],
            "normalize_fields_order_unique_words": ["order1", "order2"],
            "cluster_intra_source_is_allowed": False,
            "cluster_fields_exact": ["exact1", "exact2"],
            "cluster_fields_fuzzy": ["fuzzy1", "fuzzy2"],
            "cluster_fuzzy_threshold": 0.5,
            "mapping_sources": {"source1": 1, "source2": 2, "source3": 3},
            "mapping_acteur_types": {"atype1": 1, "atype2": 2, "atype3": 3},
        }

    @pytest.fixture
    def config_working(self, params_working) -> ClusterConfig:
        # Config qui fonctionne
        return ClusterConfig(**params_working)

    def test_working_source_ids_resolved(self, config_working):
        # Avec un gap au milieu et != total que le mapping_
        # pour démontrer qu'on à bien pioché
        assert config_working.include_source_ids == [1, 3]

    def test_working_acteur_type_ids_resolved(self, config_working):
        # Avec un gap en début et != total que le mapping_
        # pour démontrer qu'on à bien pioché
        assert config_working.include_acteur_type_ids == [2, 3]

    def test_working_no_sources_equals_all_sources(self, params_working):
        # Si aucun code source fourni alors on inclut toutes les sources
        params_working["include_sources"] = None
        config = ClusterConfig(**params_working)
        assert config.include_source_ids == [1, 2, 3]

    def test_working_cluster_fields_separate(self, config_working, params_working):
        # Par défaut on ne clusterise pas sur la même source
        assert config_working.cluster_intra_source_is_allowed is False
        assert config_working.cluster_fields_separate == ["source_id"]
        # En revanche si on autorise le clustering intra-source
        # on ne sépare pas sur la source
        params_working["cluster_intra_source_is_allowed"] = True
        config = ClusterConfig(**params_working)
        assert config.cluster_fields_separate == []

    def test_optional_include_only_if_regex_matches_nom(self, params_working):
        # On peut ne pas fournir de regex
        params_working["include_only_if_regex_matches_nom"] = None
        config = ClusterConfig(**params_working)
        assert config.include_only_if_regex_matches_nom is None

    def test_optional_exclude_if_any_field_filled(self, params_working):
        # On peut ne pas fournir de champs à exclure
        params_working["exclude_if_any_field_filled"] = None
        config = ClusterConfig(**params_working)
        assert config.exclude_if_any_field_filled == []

    def test_optional_normalize_fields_basic(self, params_working):
        # On peut ne pas fournir de champs à normaliser
        # et tous les champs présent dans les champs "fields"
        # (sauf field_all) seront rajoutés à la liste
        params_working["normalize_fields_basic"] = None
        config = ClusterConfig(**params_working)
        expected = config.fields_transformed
        diff = set(config.normalize_fields_basic) - set(expected)
        assert not diff, f"Différence: {diff}"

    def test_fields_used_separate_meta_and_data(self, params_working):
        # Les champs utilisés contiennent toujours les champs
        # internes (ex: source_id, acteur_type_id)
        config = ClusterConfig(**params_working)
        fields = [
            "source_id",
            "acteur_type_id",
            "identifiant_unique",
            "statut",
            "nombre_enfants",
        ]
        for field in fields:
            assert field in config.fields_protected
            assert field not in config.fields_transformed

    def test_fields_meta_no_duplicates(self, params_working):
        # Les champs meta ne doivent pas contenir de doublons
        params_working["fields_protected"] = ["source_id", "source_id"]
        config = ClusterConfig(**params_working)
        assert len(config.fields_protected) == len(set(config.fields_protected))

    def test_fields_data_no_duplicates(self, params_working):
        # Les champs data ne doivent pas contenir de doublons
        params_working["normalize_fields_basic"] = ["basic1", "basic1"]
        params_working["normalize_fields_no_words_size1"] = ["basic1", "basic1"]
        config = ClusterConfig(**params_working)
        assert len(config.fields_transformed) == len(set(config.fields_transformed))

    def test_optional_normalize_fields_order_unique_words(self, params_working):
        # Si aucun champ fourni => appliquer à tous les champs data
        params_working["normalize_fields_order_unique_words"] = None
        config = ClusterConfig(**params_working)
        assert config.normalize_fields_order_unique_words == config.fields_transformed

    def test_default_dry_run_is_true(self, params_working):
        # On veut forcer l'init du dry_run pour limiter
        # les risques de faux positifs (ex: valeur None
        # qui fait échouer if config.dry_run et entraine
        # des modifications)
        params_working["dry_run"] = None
        with pytest.raises(ValueError, match="dry_run à fournir"):
            ClusterConfig(**params_working)

    def test_error_must_provide_acteur_type(self, params_working):
        # Si aucun type d'acteur fourni alors on lève une erreur
        # car on ne veut pas clustering sur tous les types d'acteurs
        # à la fois = trop de risques de faux positifs
        params_working["include_acteur_types"] = []
        with pytest.raises(ValueError, match="Au moins un type d'acteur"):
            ClusterConfig(**params_working)

    def test_error_must_provide_acteur_type_none(self, params_working):
        # Variation ci-dessus avec None
        params_working["include_acteur_types"] = None
        with pytest.raises(ValueError, match="Au moins un type d'acteur"):
            ClusterConfig(**params_working)

    def test_error_source_codes_invalid(self, params_working):
        # Erreur si un code source n'existe pas dans le mapping
        params_working["include_sources"] = ["MAUVAISE SOURCE (id=666)"]
        with pytest.raises(ValueError, match="Codes non trouvés dans le mapping"):
            ClusterConfig(**params_working)

    def test_error_acteur_type_codes_invalid(self, params_working):
        # Erreur si un code acteur type n'existe pas dans le mapping
        params_working["include_acteur_types"] = ["MAUVAIS TYPE (id=666)"]
        with pytest.raises(ValueError, match="Codes non trouvés dans le mapping"):
            ClusterConfig(**params_working)

    def test_error_if_same_field_in_cluster_exact_and_fuzzy(self, params_working):
        # Because Airflow v2 UI doesn't have dynamic logic in between its params
        # (which would allow us to remove selected fields from 1 option from the other)
        # we need a config check to bail if same field selected in both exact and fuzzy
        params_working["cluster_fields_exact"] = ["foo"]
        params_working["cluster_fields_fuzzy"] = ["foo"]
        with pytest.raises(ValueError, match="Champs en double dans exact/fuzzy"):
            ClusterConfig(**params_working)

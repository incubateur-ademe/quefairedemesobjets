import pytest

from dags.clustering.tasks.business_logic.clustering_config_validate import (
    clustering_acteur_config_validate,
)


class TestClusteringActeurConfigValidate:

    @pytest.fixture(scope="session")
    def map_source_codes(self):
        return {
            "source1": 1,
            "source2": 2,
            "source3": 3,
        }

    @pytest.fixture(scope="session")
    def map_atype_codes(self):
        return {
            "type1": 1,
            "type2": 2,
            "type3": 3,
        }

    @pytest.fixture
    def params(self, map_source_codes, map_atype_codes):
        return {
            "mapping_source_id_by_code": map_source_codes,
            "mapping_acteur_type_id_by_code": map_atype_codes,
            "include_source_codes": ["source1 (id=1)"],
            "include_acteur_type_codes": ["type1 (id=1)"],
            "include_if_all_fields_filled": ["nom", "code_postal"],
            "exclude_if_any_field_filled": ["siret"],
        }

    def test_include_source_ids_invalid(self, params):
        params["include_source_codes"] = []
        with pytest.raises(
            ValueError, match="Au moins une source doit être sélectionnée"
        ):
            clustering_acteur_config_validate(**params)

    def test_include_acteur_type_ids_invalid(self, params):
        params["include_acteur_type_codes"] = []
        with pytest.raises(
            ValueError, match="Au moins un type d'acteur doit être sélectionné"
        ):
            clustering_acteur_config_validate(**params)

    def test_include_if_fields_not_empty_invalid(self, params):
        params["include_if_all_fields_filled"] = []
        with pytest.raises(
            ValueError, match="Au moins un champ non vide doit être sélectionné"
        ):
            clustering_acteur_config_validate(**params)

    def test_fields_incl_excl_invalid(self, params):
        params["include_if_all_fields_filled"] = ["nom"]
        params["exclude_if_any_field_filled"] = ["nom"]
        with pytest.raises(
            ValueError, match="Champs à la fois à inclure et à exclure: {'nom'}"
        ):
            clustering_acteur_config_validate(**params)

    def test_valid(self, params):
        clustering_acteur_config_validate(**params)

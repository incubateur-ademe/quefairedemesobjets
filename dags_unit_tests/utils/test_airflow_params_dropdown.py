import pytest

from dags.utils.airflow_params import (
    airflow_params_dropdown_from_mapping,
    airflow_params_dropdown_selected_to_ids,
)


class TestAirflowParamsDropdown:

    @pytest.fixture(scope="session")
    def mapping(self):
        return {
            "code1": 1,
            "code2": 2,
            "code3": 3,
        }

    def test_from_mapping(self, mapping):
        """Les valeurs du dropdown doivents comprendre les codes et les IDs
        pour aider à chercher via l'un ou l'autre et offrire une validation
        mutuelle via la UI Airflow (les codes peuvent se ressembler).
        """
        expected = ["code1 (id=1)", "code2 (id=2)", "code3 (id=3)"]
        actual = airflow_params_dropdown_from_mapping(mapping)
        assert actual == expected

    def test_from_mapping_exception_if_invalid(self, mapping):
        """Bien qu'on ne devrait pas avoir de doublons dans les IDs,
        sachant que les conséquences sont graves et qu'on a 0 validation
        dans Airflow, on préfère implémenter une vérification nous-même.
        """
        mapping["code4"] = 1
        with pytest.raises(ValueError, match="Mapping invalide"):
            airflow_params_dropdown_from_mapping(mapping)

    def test_to_ids(self, mapping):
        """On test avec des gaps et dans le désordre pour s'assurer
        de la robustesse de l'implémentation."""
        selected = [
            "code3 (id=3)",
            "code1 (id=1)",
        ]
        expected = [3, 1]
        actual = airflow_params_dropdown_selected_to_ids(mapping, selected)
        assert actual == expected

    def test_to_ids_exception_if_code_not_found(self, mapping):
        """Même raison que pour l'autre _exception_if_invalid: on ne
        prend pas de risque et on valide nous-même les cas invalides."""
        selected = [
            "code3 (id=3)",
            "code_not_found (id=999)",
        ]
        with pytest.raises(KeyError, match="code_not_found"):
            airflow_params_dropdown_selected_to_ids(mapping, selected)

    def test_to_ids_exception_if_dropdown_has_no_ids(self, mapping):
        """On veut s'assurer que les valeurs sélectionnées ont bien
        le format attendu avec ID_PREFIX inséré par
        airflow_params_dropdown_from_mapping."""
        selected = ["code3", "code1"]
        with pytest.raises(ValueError, match="Valeurs invalides sans ID_PREFIX"):
            airflow_params_dropdown_selected_to_ids(mapping, selected)

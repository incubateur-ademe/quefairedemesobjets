"""Tests pour le normalizer XCom.

Le serializer pandas par défaut d'Airflow 3 round-trip les DataFrames via
parquet, ce qui convertit les listes Python en numpy.ndarray — y compris à
l'intérieur de structures imbriquées (list[dict[..., list]]). Ces tests
vérifient que :

- ``_array_to_list`` ramène tout en types Python natifs, même en profondeur
- ``normalize_xcom_value`` restaure les colonnes object d'un DataFrame
- la sortie est sérialisable en JSON sans repli sur ``default=str``
"""

import io
import json

import numpy as np
import pandas as pd
from dags.shared.xcom.normalize import _array_to_list, normalize_xcom_value


class TestArrayToList:
    def test_scalar_unchanged(self):
        assert _array_to_list(42) == 42
        assert _array_to_list("foo") == "foo"
        assert _array_to_list(None) is None

    def test_nan_becomes_none(self):
        # Parquet turns None cells of object columns into float('nan')
        assert _array_to_list(float("nan")) is None
        assert _array_to_list(np.nan) is None
        # a non-nan float stays untouched
        assert _array_to_list(1.5) == 1.5

    def test_ndarray_becomes_list(self):
        result = _array_to_list(np.array(["a", "b"]))
        assert result == ["a", "b"]
        assert isinstance(result, list)

    def test_list_of_ndarrays_is_recursed(self):
        result = _array_to_list([np.array(["a"]), np.array(["b"])])
        assert result == [["a"], ["b"]]
        assert isinstance(result, list)
        assert all(isinstance(v, list) for v in result)

    def test_ndarray_inside_dict_is_recursed(self):
        result = _array_to_list({"sous_categories": np.array(["x", "y"])})
        assert result == {"sous_categories": ["x", "y"]}
        assert isinstance(result["sous_categories"], list)

    def test_list_of_dicts_with_inner_ndarray_is_recursed(self):
        """Cas exact rencontré pour ``proposition_service_codes`` après
        round-trip parquet d'Airflow 3."""
        cell = np.array(
            [
                {
                    "action": "trier",
                    "sous_categories": np.array(["petits_appareils_extincteurs"]),
                }
            ]
        )

        result = _array_to_list(cell)

        assert result == [
            {
                "action": "trier",
                "sous_categories": ["petits_appareils_extincteurs"],
            }
        ]
        assert isinstance(result, list)
        assert isinstance(result[0]["sous_categories"], list)

    def test_json_dumps_does_not_fall_back_to_str(self):
        """Check that after normalization, ``json.dumps(..., default=str)`` does not
        produce more ``"['x']"`` (repr Python) but a proper JSON array."""
        cell = np.array(
            [
                {
                    "action": "trier",
                    "sous_categories": np.array(["petits_appareils_extincteurs"]),
                }
            ]
        )

        normalized = _array_to_list(cell)

        encoded = json.dumps(normalized, default=str)
        assert (
            encoded == '[{"action": "trier", "sous_categories":'
            ' ["petits_appareils_extincteurs"]}]'
        )


class TestNormalizeXcomValue:
    def test_non_dataframe_passes_through(self):
        assert normalize_xcom_value(42) == 42
        assert normalize_xcom_value("foo") == "foo"
        assert normalize_xcom_value(None) is None
        assert normalize_xcom_value([1, 2]) == [1, 2]

    def test_dataframe_without_arrays_unchanged(self):
        df = pd.DataFrame({"a": ["x", "y"], "b": [1, 2]})
        result = normalize_xcom_value(df)
        pd.testing.assert_frame_equal(result, df)

    def test_dataframe_nan_cells_become_none(self):
        df = pd.DataFrame({"data": ['{"nom": "x"}', None]})
        # Force the None -> nan promotion parquet does on object columns
        buf = io.BytesIO()
        df.to_parquet(buf)
        buf.seek(0)
        df_after_parquet = pd.read_parquet(buf)

        result = normalize_xcom_value(df_after_parquet)

        assert result.iloc[0]["data"] == '{"nom": "x"}'
        assert result.iloc[1]["data"] is None

    def test_dataframe_with_top_level_ndarray_cell(self):
        df = pd.DataFrame({"codes": [np.array(["a", "b"]), np.array(["c"])]})

        result = normalize_xcom_value(df)

        assert result.iloc[0]["codes"] == ["a", "b"]
        assert result.iloc[1]["codes"] == ["c"]
        assert isinstance(result.iloc[0]["codes"], list)

    def test_full_parquet_round_trip_for_proposition_service_codes(self):
        """Reproduce the parquet round-trip of Airflow 3 and check that after
        ``normalize_xcom_value`` the JSON serialization is correct."""
        df = pd.DataFrame(
            {
                "identifiant_unique": ["x"],
                "proposition_service_codes": [
                    [
                        {
                            "action": "trier",
                            "sous_categories": ["petits_appareils_extincteurs"],
                        }
                    ]
                ],
            }
        )

        buf = io.BytesIO()
        df.to_parquet(buf)
        buf.seek(0)
        df_after_parquet = pd.read_parquet(buf)

        normalized = normalize_xcom_value(df_after_parquet)

        cell = normalized.iloc[0]["proposition_service_codes"]
        assert isinstance(cell, list)
        assert isinstance(cell[0]["sous_categories"], list)
        assert cell == [
            {
                "action": "trier",
                "sous_categories": ["petits_appareils_extincteurs"],
            }
        ]

        encoded = json.dumps(normalized.iloc[0].to_dict(), default=str)
        assert (
            encoded == '{"identifiant_unique": "x",'
            ' "proposition_service_codes": '
            "[{"
            '"action": "trier", "sous_categories": ["petits_appareils_extincteurs"]}'
            "]}"
        )

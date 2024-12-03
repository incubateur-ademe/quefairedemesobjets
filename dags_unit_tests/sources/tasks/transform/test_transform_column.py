import numpy as np
import pandas as pd
import pytest
from sources.tasks.transform.transform_column import clean_siren, clean_siret


class TestCleanSiret:
    @pytest.mark.parametrize(
        "siret, expected_siret",
        [
            (np.nan, ""),
            (pd.NA, ""),
            (None, ""),
            ("123456789012345", ""),
            ("98765432109876", "98765432109876"),
            ("8765432109876", "08765432109876"),
            ("AB123", ""),
        ],
    )
    def test_clean_siret(self, siret, expected_siret):
        assert clean_siret(siret) == expected_siret


class TestCleanSiren:
    @pytest.mark.parametrize(
        "siren, expected_siren",
        [
            (np.nan, ""),
            (pd.NA, ""),
            (None, ""),
            ("1234567890", ""),
            ("123456789", "123456789"),
            ("12345678", ""),
            ("", ""),
        ],
    )
    def test_clean_siren(self, siren, expected_siren):
        assert clean_siren(siren) == expected_siren

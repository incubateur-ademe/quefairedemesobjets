from unittest.mock import patch

import pandas as pd
from enrich.tasks.business_logic.normalize_acteur_cp import normalize_acteur_cp


class TestDbReadActeurCp:

    def test_normalize_acteur_cp(self):
        df = pd.DataFrame(
            {
                "identifiant_unique": ["0", "1", "2"],
                "code_postal": ["01234", "12345", "123456"],
            }
        )
        with patch(
            "enrich.tasks.business_logic.normalize_acteur_cp.clean_code_postal",
            return_value="01234",
        ) as mock_clean_code_postal:
            normalize_acteur_cp(df)
            assert mock_clean_code_postal.call_count == 3

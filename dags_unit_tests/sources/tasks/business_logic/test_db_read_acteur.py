import pandas as pd
import pytest
from sources.tasks.business_logic.db_read_acteur import db_read_acteur


class TestReadActeur:

    def test_read_acteur_raises(self):
        with pytest.raises(ValueError):
            db_read_acteur(df_normalized=pd.DataFrame())

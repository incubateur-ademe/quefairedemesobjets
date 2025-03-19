from dags.enrich.config import COLS, DBT
from dags.utils.dbt import dbt_assert_model_schema


class TestEnrichAeRgpd:

    def test_dbt(self):
        model_name = DBT.MARTS_ENRICH_AE_RGPD
        columns = [
            COLS.SIREN,
            COLS.ACTEUR_ID,
            COLS.ACTEUR_NOMS_ORIGINE,
            COLS.ACTEUR_NOMS_NORMALISES,
            COLS.ACTEUR_COMMENTAIRES,
            COLS.AE_DIRIGEANTS_NOMS,
        ]
        dbt_assert_model_schema(model_name, columns)

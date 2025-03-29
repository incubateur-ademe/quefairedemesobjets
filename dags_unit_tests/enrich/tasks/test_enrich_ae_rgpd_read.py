import pytest

from dags.enrich.config import COLS
from dags.enrich.tasks.business_logic.enrich_ae_rgpd_read import (
    enrich_ae_rgpd_read,
)

DBT_MODEL_NAME = "my_dummy_dbt_model"


@pytest.mark.django_db
class TestEnrichAeRgpdRead:

    @pytest.fixture
    def dbt_model(self):
        from django.db import connection

        sql = f"""CREATE TABLE {DBT_MODEL_NAME} (
            {COLS.ACTEUR_COMMENTAIRES} TEXT
        );

        INSERT INTO {DBT_MODEL_NAME} ({COLS.ACTEUR_COMMENTAIRES}) VALUES
            (NULL),
            ('   '),
            ('This is the first comment.'),
            ('Second comment here.'),
            ('Another comment added.');"""

        with connection.cursor() as cursor:
            cursor.execute(sql)

    def test_default(self, dbt_model):
        df = enrich_ae_rgpd_read(DBT_MODEL_NAME)
        assert df[COLS.ACTEUR_COMMENTAIRES].tolist() == [
            None,
            "   ",
            "This is the first comment.",
            "Second comment here.",
            "Another comment added.",
        ]

    def test_filter_supports_insensitive_regex(self, dbt_model):
        df = enrich_ae_rgpd_read(
            DBT_MODEL_NAME, filter_comments_contain="(second|another)"
        )
        assert df[COLS.ACTEUR_COMMENTAIRES].tolist() == [
            "Second comment here.",
            "Another comment added.",
        ]

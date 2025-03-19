import pandas as pd
import pytest

from dags.enrich.config import COLS, DBT, RGPD
from dags.enrich.tasks.business_logic.enrich_ae_rgpd_suggest import (
    enrich_ae_rgpd_suggest,
)
from dags.utils.dbt import dbt_assert_model_schema


class TestEnrichAeRgpdConfig:

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

    def test_rgpd_lock_fields_list(self):
        # A test just to lock list of fields to anonymize
        assert RGPD.ACTEUR_FIELDS_TO_ANONYMIZE == [
            "nom",
            "nom_officiel",
            "nom_commercial",
            "description",
            "email",
            "telephone",
            "adresse",
            "adresse_complement",
        ]

    def test_rgpd_lock_field_anonymized(self):
        # A test just to lock field to anonymize
        assert RGPD.ACTEUR_FIELD_ANONYMIZED == "ANONYMISE POUR RAISON RGPD"


@pytest.mark.django_db
class TestEnrichAeRgpdSuggest:

    @pytest.fixture
    def df(self):
        return pd.DataFrame(
            {
                COLS.ACTEUR_ID: ["id1", "id2"],
                COLS.ACTEUR_NOMS_ORIGINE: ["acteur1", "acteur2"],
            }
        )

    @pytest.fixture
    def acteurs(self, df):
        from qfdmo.models import Acteur

        for _, row in df.iterrows():
            Acteur.objects.create(
                identifiant_unique=row[COLS.ACTEUR_ID],
                nom=row[COLS.ACTEUR_NOMS_ORIGINE],
            )

    @pytest.fixture
    def suggestions(self, df, acteurs):
        return enrich_ae_rgpd_suggest(
            df=df,
            identifiant_action="my_action_id",
            identifiant_execution="my_execution_id",
            dry_run=True,
        )

    @pytest.fixture
    def suggest(self, suggestions):
        return suggestions[0]

    def test_one_suggestion_per_acteur(self, df, suggestions):
        assert len(suggestions) == len(df)

    def test_one_change_per_suggestion(self, suggest):
        # 1 change per acteur, we don't group acteurs together
        # even if they have identical SIREN or SIRET
        assert len(suggest["suggestion"]["changes"]) == 1

    def test_suggestion_change_structure(self, suggest):
        # The changes being sensitive, this test intentionnally
        # hardcodes the structure of the suggestion so we need
        # to udpate tests with intention when changing the DAG
        change = suggest["suggestion"]["changes"][0]
        assert change["model_name"] == "acteur_update_data"
        assert change["model_params"] == {
            "id": "id1",
            "data": {
                "nom": "ANONYMISE POUR RAISON RGPD",
                "nom_officiel": "ANONYMISE POUR RAISON RGPD",
                "nom_commercial": "ANONYMISE POUR RAISON RGPD",
                "description": "ANONYMISE POUR RAISON RGPD",
                "email": "ANONYMISE POUR RAISON RGPD",
                "telephone": "ANONYMISE POUR RAISON RGPD",
                "adresse": "ANONYMISE POUR RAISON RGPD",
                "adresse_complement": "ANONYMISE POUR RAISON RGPD",
                "statut": "INACTIF",
            },
        }

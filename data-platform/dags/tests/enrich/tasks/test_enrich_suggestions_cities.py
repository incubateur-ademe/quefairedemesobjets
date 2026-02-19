import pandas as pd
import pytest
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_read import df_filter
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)


@pytest.mark.django_db
class TestEnrichSuggestionsCities:

    @pytest.fixture
    def config(self):
        from enrich.config.models import EnrichActeursVillesConfig

        return EnrichActeursVillesConfig(
            dry_run=False,
            filter_equals__acteur_statut="ACTIF",
        )

    @pytest.fixture
    def df_new(self):
        return pd.DataFrame(
            {
                # last entry is INACTIF to test acteur status filter
                COLS.SUGGEST_COHORT: [COHORTS.VILLES_NEW] * 3,
                COLS.SUGGEST_VILLE: ["new town 1", "new town 2", "closed"],
                COLS.ACTEUR_ID: ["new1", "new2", "closed 1"],
                COLS.ACTEUR_ADRESSE: ["1 rue", "2 rue", "3 rue"],
                COLS.ACTEUR_CODE_POSTAL: ["12345", "67890", "54321"],
                COLS.ACTEUR_VILLE: ["old town 1", "old town 2", "closed"],
                COLS.ACTEUR_STATUT: ["ACTIF", "ACTIF", "INACTIF"],
            }
        )

    @pytest.fixture
    def df_typo(self):
        return pd.DataFrame(
            {
                # last entry is INACTIF to test acteur status filter
                COLS.SUGGEST_COHORT: [COHORTS.VILLES_TYPO] * 3,
                COLS.SUGGEST_VILLE: ["Paris", "Laval", "closed"],
                COLS.ACTEUR_ID: ["typo1", "typo2", "closed 2"],
                COLS.ACTEUR_ADRESSE: ["1 rue", "2 rue", "3 rue"],
                COLS.ACTEUR_CODE_POSTAL: ["12345", "67890", "54321"],
                COLS.ACTEUR_VILLE: ["Pâris", "Lâval", "closed"],
                COLS.ACTEUR_STATUT: ["ACTIF", "ACTIF", "INACTIF"],
            }
        )

    @pytest.fixture
    def df_new_filtered(self, df_new, config):
        # To test that config works (e.g. filter_equals__acteur_statut)
        return df_filter(df_new, config.filters)

    @pytest.fixture
    def df_typo_filtered(self, df_typo, config):
        # To test that config works (e.g. filter_equals__acteur_statut)
        return df_filter(df_typo, config.filters)

    @pytest.fixture
    def acteurs(self, df_new_filtered, df_typo_filtered):
        # Creating acteurs as presence required to apply changes
        from unit_tests.qfdmo.acteur_factory import ActeurFactory

        for _, row in pd.concat([df_new_filtered, df_typo_filtered]).iterrows():
            ActeurFactory(
                identifiant_unique=row[COLS.ACTEUR_ID],
                ville=row[COLS.ACTEUR_VILLE],
            )

    def test_cohort_new(self, acteurs, df_new):
        from data.models.suggestion import Suggestion, SuggestionCohorte
        from qfdmo.models import RevisionActeur

        # Write suggestions to DB
        enrich_dbt_model_to_suggestions(
            df=df_new,
            cohort=COHORTS.VILLES_NEW,
            identifiant_action="test_new",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_new")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 2

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        # 2 revisions should be created but not parent
        new1 = RevisionActeur.objects.get(pk="new1")
        assert new1.ville == "new town 1"

        new2 = RevisionActeur.objects.get(pk="new2")
        assert new2.ville == "new town 2"

    def test_cohort_typo(self, acteurs, df_typo):
        from data.models.suggestion import Suggestion, SuggestionCohorte
        from qfdmo.models import RevisionActeur

        # Write suggestions to DB
        enrich_dbt_model_to_suggestions(
            df=df_typo,
            cohort=COHORTS.VILLES_TYPO,
            identifiant_action="test_typo",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_typo")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 2

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        typo1 = RevisionActeur.objects.get(pk="typo1")
        assert typo1.ville == "Paris"

        typo2 = RevisionActeur.objects.get(pk="typo2")
        assert typo2.ville == "Laval"

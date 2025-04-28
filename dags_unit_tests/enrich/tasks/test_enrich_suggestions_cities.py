import pandas as pd
import pytest
from enrich.config import COHORTS, COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)


@pytest.mark.django_db
class TestEnrichSuggestionsCities:

    @pytest.fixture
    def df_new(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.VILLES_NEW] * 2,
                COLS.SUGGEST_VILLE: ["new town 1", "new town 2"],
                COLS.ACTEUR_ID: ["new1", "new2"],
                COLS.ACTEUR_VILLE: ["old town 1", "old town 2"],
            }
        )

    @pytest.fixture
    def df_typo(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.VILLES_TYPO] * 2,
                COLS.SUGGEST_VILLE: ["Paris", "Laval"],
                COLS.ACTEUR_ID: ["typo1", "typo2"],
                COLS.ACTEUR_VILLE: ["Pâris", "Lâval"],
            }
        )

    @pytest.fixture
    def acteurs(self, df_new, df_typo):
        # Creating acteurs as presence required to apply changes
        from unit_tests.qfdmo.acteur_factory import ActeurFactory

        for _, row in pd.concat([df_new, df_typo]).iterrows():
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

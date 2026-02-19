import pandas as pd
import pytest
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

from data.models.changes.acteur_rgpd_anonymize import ACTEUR_FIELDS_TO_ANONYMIZE


@pytest.mark.django_db
class TestEnrichSuggestionsRgpd:

    @pytest.fixture
    def df_rgpd(self):
        return pd.DataFrame(
            {
                COLS.SUGGEST_COHORT: [COHORTS.RGPD] * 2,
                COLS.ACTEUR_ID: ["rgpd1", "rgpd2"],
                COLS.ACTEUR_STATUT: ["ACTIF"] * 2,
                COLS.ACTEUR_NOMS_ORIGINE: ["nom rgpd1", "nom rgpd2"],
                COLS.ACTEUR_NOM: ["nom rgpd1", "nom rgpd2"],
            }
        )

    @pytest.fixture
    def acteurs(self, df_rgpd):
        # The point of the RGPD pipeline is to anonymize the data
        # everywhere in our DB, thus it won't follow the usual pattern
        # of creating/updating a revision only, it overwrites acteurs
        # wherever they are found WITHOUT creating revivisions
        from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory

        # rgpd1 only in base
        ActeurFactory(identifiant_unique="rgpd1", nom="nom rgpd1")
        # rgpd2 in both base and revision
        ActeurFactory(identifiant_unique="rgpd2", nom="nom rgpd2")
        RevisionActeurFactory(pk="rgpd2", nom="nom rgpd2")

    @pytest.fixture
    def suggestions_applied(self, acteurs, df_rgpd):
        """Generating and applying suggestions"""
        from data.models.suggestion import Suggestion, SuggestionCohorte

        enrich_dbt_model_to_suggestions(
            df=df_rgpd,
            cohort=COHORTS.RGPD,
            identifiant_action="test_rgpd",
            dry_run=False,
        )
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_rgpd")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 2
        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

    def test_changed_only_in_base(self, suggestions_applied):
        # Test that the acteur in base is changed WITHOUT creating a revision
        from qfdmo.models import Acteur

        rgpd1 = Acteur.objects.get(pk="rgpd1")
        assert all(
            getattr(rgpd1, field) == value
            for field, value in ACTEUR_FIELDS_TO_ANONYMIZE.items()
        )

    def test_changed_in_both(self, suggestions_applied):
        # Test that the acteur in both base and revision is changed
        from qfdmo.models import Acteur, RevisionActeur

        rgpd2 = Acteur.objects.get(pk="rgpd2")
        assert all(
            getattr(rgpd2, field) == value
            for field, value in ACTEUR_FIELDS_TO_ANONYMIZE.items()
        )
        rgpd2_rev = RevisionActeur.objects.get(pk="rgpd2")
        assert all(
            getattr(rgpd2_rev, field) == value
            for field, value in ACTEUR_FIELDS_TO_ANONYMIZE.items()
        )

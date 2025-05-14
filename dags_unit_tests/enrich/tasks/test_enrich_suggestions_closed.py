import re
from datetime import datetime, timezone

import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

from qfdmo.models.acteur import Acteur

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@pytest.mark.django_db
class TestEnrichActeursClosedSuggestions:

    @pytest.fixture
    def source(self):
        from qfdmo.models import Source

        return Source.objects.create(code="s1")

    @pytest.fixture
    def atype(self):
        from qfdmo.models import ActeurType

        return ActeurType.objects.create(code="at1")

    @pytest.fixture
    def parent(self):
        from unit_tests.qfdmo.acteur_factory import RevisionActeurFactory

        return RevisionActeurFactory(
            nom="Parent",
            adresse="Adresse parent",
            code_postal="12345",
            ville="Ville parent",
        )

    @pytest.fixture
    def df_not_replaced(self, atype, source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a01", "a02"],
                COLS.ACTEUR_ID_EXTERNE: ["ext_a01", "ext_a02"],
                COLS.ACTEUR_SIRET: ["00000000000001", "00000000000002"],
                COLS.ACTEUR_NOM: ["AVANT a01", "AVANT a02"],
                COLS.ACTEUR_TYPE_ID: [atype.pk, atype.pk],
                COLS.ACTEUR_SOURCE_ID: [source.pk, source.pk],
                COLS.SUGGEST_COHORT: [COHORTS.CLOSED_NOT_REPLACED] * 2,
            }
        )

    @pytest.fixture
    def df_replaced(self, atype, source, parent):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a1", "a2", "a3"],
                COLS.ACTEUR_ID_EXTERNE: ["ext_a1", "ext_a2", "ext_a3"],
                # We test 1 acteur of each cohort with a parent, and
                # the case with no parent
                COLS.ACTEUR_PARENT_ID: [parent.pk, parent.pk, None],
                COLS.ACTEUR_SIRET: [
                    "11111111100001",
                    "22222222200001",
                    "44444444400001",
                ],
                COLS.ACTEUR_TYPE_ID: [atype.pk, atype.pk, atype.pk],
                COLS.ACTEUR_SOURCE_ID: [source.pk, source.pk, source.pk],
                COLS.ACTEUR_LONGITUDE: [1, 1, 1],
                COLS.ACTEUR_LATITUDE: [2, 2, 2],
                # Replacement data
                COLS.SUGGEST_SIRET: [
                    "11111111100002",
                    "33333333300001",
                    "55555555500001",
                ],
                COLS.SUGGEST_SIREN: ["111111111", "333333333", "555555555"],
                COLS.SUGGEST_NOM: ["APRES a1", "APRES a2", "APRES a3"],
                COLS.SUGGEST_COHORT: [
                    COHORTS.CLOSED_REP_SAME_SIREN,
                    COHORTS.CLOSED_REP_OTHER_SIREN,
                    COHORTS.CLOSED_REP_OTHER_SIREN,
                ],
                COLS.SUGGEST_ADRESSE: ["Adresse1", "Adresse2", "Adresse3"],
                COLS.SUGGEST_CODE_POSTAL: ["12345", "67890", "12345"],
                COLS.SUGGEST_VILLE: ["Ville1", "Ville2", "Ville3"],
                COLS.SUGGEST_NAF: ["naf1", "naf2", "naf3"],
                COLS.SUGGEST_LONGITUDE: [1, 2, 3],
                COLS.SUGGEST_LATITUDE: [11, 22, 33],
                COLS.SUGGEST_ACTEUR_TYPE_ID: [atype.pk, atype.pk, atype.pk],
            }
        )

    def test_df_replaced(self, df_replaced):
        assert sorted(df_replaced[COLS.SUGGEST_COHORT].unique()) == sorted(
            [
                COHORTS.CLOSED_REP_SAME_SIREN,
                COHORTS.CLOSED_REP_OTHER_SIREN,
            ]
        )

    @pytest.fixture
    def df_replaced_meme_siret(self, df_replaced):
        return df_replaced[
            df_replaced[COLS.SUGGEST_COHORT] == COHORTS.CLOSED_REP_SAME_SIREN
        ]

    @pytest.fixture
    def df_replaced_autre_siret(self, df_replaced):
        return df_replaced[
            df_replaced[COLS.SUGGEST_COHORT] == COHORTS.CLOSED_REP_OTHER_SIREN
        ]

    @pytest.fixture
    def acteurs(self, df_not_replaced, df_replaced, atype, source):
        # Creating acteurs as presence required to apply changes
        from qfdmo.models import Acteur

        df_concat = pd.concat([df_not_replaced, df_replaced])
        for _, row in df_concat.iterrows():
            acteur = Acteur(
                identifiant_unique=row[COLS.ACTEUR_ID],
                identifiant_externe=row[COLS.ACTEUR_ID_EXTERNE],
                nom=f"AVANT {row[COLS.ACTEUR_ID]}",
                acteur_type=atype,
                source=source,
                location=Point(
                    x=row[COLS.ACTEUR_LONGITUDE], y=row[COLS.ACTEUR_LATITUDE]
                ),
            )
            acteur.save()
            # Check that acteur has been properly created
            acteur = Acteur.objects.get(identifiant_unique=row[COLS.ACTEUR_ID])
            assert acteur.identifiant_externe == row[COLS.ACTEUR_ID_EXTERNE]
            assert acteur.nom == f"AVANT {row[COLS.ACTEUR_ID]}"
            assert acteur.acteur_type == atype
            assert acteur.source == source

    def test_cohorte_not_replaced(self, acteurs, df_not_replaced):
        from data.models.suggestion import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

        # Write suggestions to DB
        enrich_dbt_model_to_suggestions(
            df=df_not_replaced,
            cohort=COHORTS.CLOSED_NOT_REPLACED,
            identifiant_action="test_not_replaced",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_not_replaced")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 2

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes: both acteurs are closed with only relevant
        # fields updated
        for id in ["a01", "a02"]:
            closed = RevisionActeur.objects.get(pk=id)
            assert closed.statut == ActeurStatus.INACTIF
            assert closed.parent is None
            assert closed.parent_reason == ""  # consequence of empty strings in DB
            assert closed.siret_is_closed is True

    def check_replaced_acteur(
        self,
        id,
        id_ext,
        siret_closed,
        siret_new,
        parent,
        parent_reason,
        source,
        acteur_type,
    ):
        """Utility to check replaced acteur to avoid repetition"""
        from qfdmo.models import ActeurStatus, RevisionActeur

        # Closed acteur
        a_closed = Acteur.objects.get(pk=id)
        ra_closed = RevisionActeur.objects.get(pk=id)
        assert a_closed.statut == ActeurStatus.INACTIF
        assert ra_closed.statut == ActeurStatus.INACTIF
        assert ra_closed.siret_is_closed or a_closed.siret_is_closed

        # The new acteur which about from siret_is_closed AND
        # identifiant_externe has the same data as the closed acteur
        a_new = Acteur.objects.filter(
            identifiant_externe=id_ext, statut=ActeurStatus.ACTIF
        ).first()
        ra_new = RevisionActeur.objects.filter(
            identifiant_unique=a_new.identifiant_unique
        ).first()
        assert a_new is not None
        assert ra_new is not None
        # ID is concatenation of closed acteur ID, new siret and today's datetime
        assert re.search(
            f"^{id}_{TODAY.replace('-', '')}[0-9]{{6}}$", a_new.identifiant_unique
        )
        assert a_new.statut == ActeurStatus.ACTIF
        assert ra_new.statut == ActeurStatus.ACTIF
        assert a_new.siret == siret_new
        assert ra_new.siret == siret_new
        assert a_new.siret_is_closed is False  # we have detected no closure yet
        assert ra_new.siret_is_closed is False  # we have detected no closure yet

        # foreign keys are iso with the closed acteur
        assert a_new.source.pk == source.pk  # type: ignore
        assert a_new.acteur_type.pk == acteur_type.pk
        assert a_new.identifiant_externe == id_ext
        # Explanation as to why
        print(f"{parent_reason} === {ra_new.parent_reason}")
        assert ra_new.parent_reason == parent_reason

    def test_cohorte_meme_siren(
        self, acteurs, parent, atype, source, df_replaced_meme_siret
    ):
        from data.models.suggestion import Suggestion, SuggestionCohorte

        # Write suggestions to DB
        enrich_dbt_model_to_suggestions(
            df=df_replaced_meme_siret,
            cohort=COHORTS.CLOSED_REP_SAME_SIREN,
            identifiant_action="test_meme_siren",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_meme_siren")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 1

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Closed acteur
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.check_replaced_acteur(
            id="a1",
            id_ext="ext_a1",
            siret_closed="11111111100001",
            siret_new="11111111100002",
            parent=parent,
            parent_reason=(
                "Nouvelle version de l'acteur conservée suite aux modifications:"
                f" SIRET 11111111100001 détecté le {today} comme fermé dans AE,"
                " remplacé par SIRET 11111111100002"
            ),
            source=source,
            acteur_type=atype,
        )

    def test_cohorte_autre_siren(
        self, acteurs, parent, atype, source, df_replaced_autre_siret
    ):
        from data.models.suggestion import Suggestion, SuggestionCohorte

        # Write suggestions to DB
        enrich_dbt_model_to_suggestions(
            df=df_replaced_autre_siret,
            cohort=COHORTS.CLOSED_REP_OTHER_SIREN,
            identifiant_action="test_autre_siren",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_autre_siren")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)

        # 2 suggestions containing 2 changes (inactive + new)
        assert len(suggestions) == 2
        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.check_replaced_acteur(
            id="a2",
            id_ext="ext_a2",
            siret_closed="22222222200001",
            siret_new="33333333300001",
            parent=parent,
            parent_reason=(
                "Nouvelle version de l'acteur conservée suite aux modifications:"
                f" SIRET 22222222200001 détecté le {today} comme fermé dans AE,"
                " remplacé par SIRET 33333333300001"
            ),
            source=source,
            acteur_type=atype,
        )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.check_replaced_acteur(
            id="a3",
            id_ext="ext_a3",
            siret_closed="44444444400001",
            siret_new="55555555500001",
            parent=parent,
            # This closed acteur has no parent so there should be no parent_reason
            parent_reason=(
                "Nouvelle version de l'acteur conservée suite aux modifications:"
                f" SIRET 44444444400001 détecté le {today} comme fermé dans AE,"
                " remplacé par SIRET 55555555500001"
            ),
            source=source,
            acteur_type=atype,
        )

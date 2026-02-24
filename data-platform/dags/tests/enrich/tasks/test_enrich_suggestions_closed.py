from datetime import datetime, timezone

import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

from data.models.suggestion import Suggestion, SuggestionCohorte
from qfdmo.models.acteur import Acteur, ActeurStatus, RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    SourceFactory,
)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@pytest.mark.django_db
class TestEnrichActeursClosedSuggestions:

    @pytest.fixture
    def source(self):
        return SourceFactory(code="s1")

    @pytest.fixture
    def atype(self):
        return ActeurTypeFactory(code="at1")

    @pytest.fixture
    def df_not_replaced(self, atype, source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a01", "a02"],
                COLS.ACTEUR_ID_EXTERNE: ["ext_a01", "ext_a02"],
                COLS.ACTEUR_SIRET: ["00000000000001", "00000000000002"],
                COLS.ACTEUR_NOM: ["AVANT a01", "AVANT a02"],
                COLS.ACTEUR_STATUT: ["ACTIF", "ACTIF"],
                COLS.ACTEUR_ADRESSE: ["1 rue Nantes", "2 rue Nantes"],
                COLS.ACTEUR_CODE_POSTAL: ["35001", "35002"],
                COLS.ACTEUR_VILLE: ["Rennes", "Rennes"],
                COLS.ACTEUR_TYPE_ID: [atype.pk, atype.pk],
                COLS.ACTEUR_SOURCE_ID: [source.pk, source.pk],
                COLS.SUGGEST_COHORT: [COHORTS.CLOSED_NOT_REPLACED_UNITE] * 2,
            }
        )

    @pytest.fixture
    def df_replaced(self, atype, source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a1", "a2", "a3"],
                COLS.ACTEUR_NOM: ["nom 1", "nom 2", "nom 3"],
                COLS.ACTEUR_STATUT: ["ACTIF", "ACTIF", "ACTIF"],
                COLS.ACTEUR_ADRESSE: ["1 rue Nantes", "2 rue Nantes", "3 rue Nantes"],
                COLS.ACTEUR_CODE_POSTAL: ["35001", "35002", "35003"],
                COLS.ACTEUR_VILLE: ["Rennes", "Rennes", "Rennes"],
                COLS.ACTEUR_ID_EXTERNE: ["ext_a1", "ext_a2", "ext_a3"],
                # We test 1 acteur of each cohort with a parent, and
                # the case with no parent
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

        df_concat = pd.concat([df_not_replaced, df_replaced])
        for _, row in df_concat.iterrows():
            acteur = ActeurFactory(
                identifiant_unique=row[COLS.ACTEUR_ID],
                identifiant_externe=row[COLS.ACTEUR_ID_EXTERNE],
                nom=f"AVANT {row[COLS.ACTEUR_ID]}",
                siret=row[COLS.ACTEUR_SIRET],
                siren=row[COLS.ACTEUR_SIRET][:9],
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
            cohort=COHORTS.CLOSED_NOT_REPLACED_UNITE,
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
            assert closed.parent_reason == (
                f"Modifications de l'acteur le {TODAY}: "
                f"SIRET {'00000000000001' if id == 'a01' else '00000000000002'} détecté"
                " comme fermé dans AE, Pas de remplacement"
            )
            assert closed.siret_is_closed is True

    def test_cohorte_meme_siren(self, acteurs, df_replaced_meme_siret):

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

        acteur = Acteur.objects.get(pk="a1")
        assert acteur.statut == ActeurStatus.ACTIF
        assert acteur.siret == "11111111100001"
        assert acteur.siren == "111111111"

        revision = RevisionActeur.objects.get(pk="a1")
        assert revision.statut == ActeurStatus.ACTIF
        assert revision.siret == "11111111100002"
        assert acteur.siren == "111111111"
        assert revision.parent is None
        assert revision.parent_reason == (
            f"Modifications de l'acteur le {TODAY}: SIRET 11111111100001 détecté comme"
            " fermé dans AE, remplacé par le SIRET 11111111100002"
        )
        assert revision.siret_is_closed is False

    def test_cohorte_autre_siren(self, acteurs, df_replaced_autre_siret):
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

        acteur = Acteur.objects.get(pk="a2")
        assert acteur.statut == ActeurStatus.ACTIF
        assert acteur.siret == "22222222200001"
        assert acteur.siren == "222222222"

        revision = RevisionActeur.objects.get(pk="a2")
        assert revision.statut == ActeurStatus.ACTIF
        assert revision.siret == "33333333300001"
        assert revision.siren == "333333333"
        assert revision.parent is None
        assert revision.parent_reason == (
            f"Modifications de l'acteur le {TODAY}: SIRET 22222222200001 détecté comme"
            " fermé dans AE, remplacé par le SIRET 33333333300001"
        )
        assert revision.siret_is_closed is False

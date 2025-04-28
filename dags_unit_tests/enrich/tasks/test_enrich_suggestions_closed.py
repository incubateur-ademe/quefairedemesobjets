from datetime import datetime, timezone

import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

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
        acteur_ids = df_concat[COLS.ACTEUR_ID].tolist()
        for acteur_id in acteur_ids:
            Acteur.objects.create(
                identifiant_unique=acteur_id,
                nom=f"AVANT {acteur_id}",
                acteur_type=atype,
                source=source,
                location=Point(x=0, y=0),
            )

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

        # Verify changes
        # 2 revisions should be created but not parent
        a01 = RevisionActeur.objects.get(pk="a01")
        assert a01.statut == ActeurStatus.INACTIF
        assert a01.parent is None
        assert a01.parent_reason == ""  # consequence of empty strings in DB
        assert a01.siret_is_closed is True
        assert a01.identifiant_externe == "ext_a01"

        a02 = RevisionActeur.objects.get(pk="a02")
        assert a02.statut == ActeurStatus.INACTIF
        assert a02.parent is None
        assert a02.parent_reason == ""
        assert a02.siret_is_closed is True
        assert a02.identifiant_externe == "ext_a02"

    def test_cohorte_meme_siren(
        self, acteurs, parent, atype, source, df_replaced_meme_siret
    ):
        from data.models.suggestion import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

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
        closed = RevisionActeur.objects.get(pk="a1")
        assert closed.statut == ActeurStatus.INACTIF
        assert closed.parent_reason == (
            f"SIRET 11111111100001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 11111111100002"
        )
        assert closed.siret_is_closed is True
        assert closed.location.x == 1
        assert closed.location.y == 11

        # Replacement acteur
        new = RevisionActeur.objects.get(identifiant_externe="ext_a1")
        assert new.statut == ActeurStatus.ACTIF
        assert new.parent.pk == parent.pk
        assert new.source.pk == source.pk
        assert "même parent que l'ancien enfant" in new.parent_reason

    def test_cohorte_autre_siren(self, acteurs, parent, df_replaced_autre_siret):
        from data.models.suggestion import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

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
        assert len(suggestions) == 2  # (1 parent + 1 child) x 2 acteurs fermés

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        # TODO: repeat the comparison between closed and replacements
        # for both acteurs, the only different is the first has a parent
        # and not the second
        child = RevisionActeur.objects.get(pk="a2")
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent.pk == parent.pk
        assert child.parent_reason == (
            f"SIRET 22222222200001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 33333333300001"
        )
        assert child.siret_is_closed is True
        assert child.location.x == 2
        assert child.location.y == 22
        assert child.identifiant_externe == "ext_a2"

        child = RevisionActeur.objects.get(pk="a3")
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent is None  # 2nd child had no parent
        assert child.parent_reason == (
            f"SIRET 44444444400001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 55555555500001"
        )
        assert child.location.x == 3
        assert child.location.y == 33
        assert child.identifiant_externe == "ext_a3"

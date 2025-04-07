from datetime import datetime, timezone

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from django.contrib.gis.geos import Point
from rich import print

from dags.enrich.config import COHORTS, COLS
from dags.enrich.tasks.business_logic.enrich_acteurs_closed_suggestions import (
    enrich_acteurs_closed_suggestions,
)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

COHORT_DEBUG_COLS = ["identifiant_action", "identifiant_execution", "type_action"]


@pytest.mark.django_db
class TestEnrichActeursClosedSuggestions:

    @pytest.fixture
    def acteur_source(self):
        from data.models import Source

        return Source.objects.create(code="s1")

    @pytest.fixture
    def acteur_type(self):
        from qfdmo.models import ActeurType

        return ActeurType.objects.create(code="at1")

    @pytest.fixture
    def df_not_replaced(self, acteur_type, acteur_source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a01", "a02"],
                COLS.ACTEUR_SIRET: ["00000000000001", "00000000000002"],
                COLS.ACTEUR_NOM: ["AVANT a01", "AVANT a02"],
                COLS.ACTEUR_TYPE: [acteur_type.pk, acteur_type.pk],
                COLS.ACTEUR_SOURCE: [acteur_source.pk, acteur_source.pk],
            }
        )

    @pytest.fixture
    def df_replaced(self, acteur_type, acteur_source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a1", "a2"],
                COLS.ACTEUR_SIRET: ["11111111100001", "22222222200001"],
                COLS.ACTEUR_TYPE: [acteur_type.pk, acteur_type.pk],
                COLS.ACTEUR_SOURCE: [acteur_source.pk, acteur_source.pk],
                # Replacement data
                COLS.REMPLACER_SIRET: ["11111111100002", "33333333300001"],
                COLS.REMPLACER_NOM: ["APRES a1", "APRES a2"],
                COLS.REMPLACER_COHORTE: ["meme_siret", "autre_siret"],
                COLS.REMPLACER_ADRESSE: ["Adresse1", "Adresse2"],
                COLS.REMPLACER_CODE_POSTAL: ["12345", "67890"],
                COLS.REMPLACER_VILLE: ["Ville1", "Ville2"],
                COLS.REMPLACER_NAF: ["naf1", "naf2"],
            }
        )

    def test_df_replaced(self, df_replaced):
        assert sorted(df_replaced[COLS.REMPLACER_COHORTE].unique()) == sorted(
            [
                "meme_siret",
                "autre_siret",
            ]
        )

    @pytest.fixture
    def df_replaced_meme_siret(self, df_replaced):
        return df_replaced[df_replaced[COLS.REMPLACER_COHORTE] == "meme_siret"]

    @pytest.fixture
    def df_replaced_autre_siret(self, df_replaced):
        return df_replaced[df_replaced[COLS.REMPLACER_COHORTE] == "autre_siret"]

    @pytest.fixture
    def acteurs(self, df_not_replaced, df_replaced, acteur_type, acteur_source):
        # Creating acteurs as presence required to apply changes
        from qfdmo.models import Acteur

        df_concat = pd.concat([df_not_replaced, df_replaced])
        acteur_ids = df_concat[COLS.ACTEUR_ID].tolist()
        for acteur_id in acteur_ids:
            Acteur.objects.create(
                identifiant_unique=acteur_id,
                nom=f"AVANT {acteur_id}",
                acteur_type=acteur_type,
                source=acteur_source,
                location=Point(x=0, y=0),
            )

    def DISABLED_test_cohorte_not_replaced(self, acteurs, df_not_replaced):
        from data.models import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

        # Write suggestions to DB
        enrich_acteurs_closed_suggestions(
            df=df_not_replaced,
            cohort_type=COHORTS.ACTEURS_CLOSED_NOT_REPLACED,
            identifiant_action="test_not_replaced",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        print(list(SuggestionCohorte.objects.all().values(*COHORT_DEBUG_COLS)))
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
        assert a01.parent_reason is None
        assert a01.siret_is_closed is True

        a02 = RevisionActeur.objects.get(pk="a02")
        assert a02.statut == ActeurStatus.INACTIF
        assert a02.parent is None
        assert a02.parent_reason is None
        assert a02.siret_is_closed is True

    def test_cohorte_meme_siren(self, acteurs, df_replaced_meme_siret):
        from data.models import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

        # Write suggestions to DB
        enrich_acteurs_closed_suggestions(
            df=df_replaced_meme_siret,
            cohort_type=COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
            identifiant_action="test_meme_siren",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        print(list(SuggestionCohorte.objects.all().values(*COHORT_DEBUG_COLS)))
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_meme_siren")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 1

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        # 1 parent should be created in revision with replacement data
        # 1 child should be created in revision with status=INACT and parent_id pointing
        parent_id = parent_id_generate(["11111111100002"])
        parent = RevisionActeur.objects.get(pk=parent_id)
        assert parent.nom == "APRES a1"
        assert parent.adresse == "Adresse1"
        assert parent.code_postal == "12345"
        assert parent.ville == "Ville1"
        assert parent.naf_principal == "naf1"

        child = RevisionActeur.objects.get(pk="a1")
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent == parent
        assert (
            child.parent_reason
            == f"""SIRET 11111111100001 détecté le {TODAY} comme fermé dans AE,
                    remplacé par SIRET 11111111100002"""
        )
        assert child.siret_is_closed is True

    def test_cohorte_autre_siren(self, acteurs, df_replaced_autre_siret):
        from data.models import Suggestion, SuggestionCohorte
        from qfdmo.models import ActeurStatus, RevisionActeur

        # Write suggestions to DB
        enrich_acteurs_closed_suggestions(
            df=df_replaced_autre_siret,
            cohort_type=COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
            identifiant_action="test_autre_siren",
            dry_run=False,
        )

        # Check suggestions have been written to DB
        print(list(SuggestionCohorte.objects.all().values(*COHORT_DEBUG_COLS)))
        cohort = SuggestionCohorte.objects.get(identifiant_action="test_autre_siren")
        suggestions = Suggestion.objects.filter(suggestion_cohorte=cohort)
        assert len(suggestions) == 1

        # Apply suggestions
        for suggestion in suggestions:
            suggestion.apply()

        # Verify changes
        # 1 parent should be created in revision with replacement data
        # 1 child should be created in revision with status=INACT and parent_id pointing
        parent_id = parent_id_generate(["33333333300001"])
        parent = RevisionActeur.objects.get(pk=parent_id)
        assert parent.nom == "APRES a2"
        assert parent.adresse == "Adresse2"
        assert parent.code_postal == "67890"
        assert parent.ville == "Ville2"
        assert parent.naf_principal == "naf2"

        child = RevisionActeur.objects.get(pk="a2")
        assert child.nom == "AVANT a2"
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent == parent
        assert (
            child.parent_reason
            == f"""SIRET 22222222200001 détecté le {TODAY} comme fermé dans AE,
                    remplacé par SIRET 33333333300001"""
        )
        assert child.siret_is_closed is True

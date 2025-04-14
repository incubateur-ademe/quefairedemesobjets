from datetime import datetime, timezone

import pandas as pd
import pytest
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from django.contrib.gis.geos import Point
from enrich.config import COHORTS, COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    enrich_dbt_model_to_suggestions,
)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


@pytest.mark.django_db
class TestEnrichActeursClosedSuggestions:

    @pytest.fixture
    def source(self):
        from data.models import Source

        return Source.objects.create(code="s1")

    @pytest.fixture
    def atype(self):
        from qfdmo.models import ActeurType

        return ActeurType.objects.create(code="at1")

    @pytest.fixture
    def df_not_replaced(self, atype, source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a01", "a02"],
                COLS.ACTEUR_SIRET: ["00000000000001", "00000000000002"],
                COLS.ACTEUR_NOM: ["AVANT a01", "AVANT a02"],
                COLS.ACTEUR_TYPE_ID: [atype.pk, atype.pk],
                COLS.ACTEUR_SOURCE_ID: [source.pk, source.pk],
                COLS.SUGGEST_COHORT_CODE: [COHORTS.CLOSED_NOT_REPLACED.code] * 2,
                COLS.SUGGEST_COHORT_LABEL: [COHORTS.CLOSED_NOT_REPLACED.label] * 2,
            }
        )

    @pytest.fixture
    def df_replaced(self, atype, source):
        return pd.DataFrame(
            {
                # Acteurs data
                COLS.ACTEUR_ID: ["a1", "a2", "a3"],
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
                COLS.REMPLACER_SIRET: [
                    "11111111100002",
                    "33333333300001",
                    "55555555500001",
                ],
                COLS.REMPLACER_NOM: ["APRES a1", "APRES a2", "APRES a3"],
                COLS.SUGGEST_COHORT_CODE: [
                    COHORTS.CLOSED_REP_SAME_SIREN.code,
                    COHORTS.CLOSED_REP_OTHER_SIREN.code,
                    COHORTS.CLOSED_REP_OTHER_SIREN.code,
                ],
                COLS.SUGGEST_COHORT_LABEL: [
                    COHORTS.CLOSED_REP_SAME_SIREN.label,
                    COHORTS.CLOSED_REP_OTHER_SIREN.label,
                    COHORTS.CLOSED_REP_OTHER_SIREN.label,
                ],
                COLS.REMPLACER_ADRESSE: ["Adresse1", "Adresse2", "Adresse3"],
                COLS.REMPLACER_CODE_POSTAL: ["12345", "67890", "12345"],
                COLS.REMPLACER_VILLE: ["Ville1", "Ville2", "Ville3"],
                COLS.REMPLACER_NAF: ["naf1", "naf2", "naf3"],
            }
        )

    def test_df_replaced(self, df_replaced):
        assert sorted(df_replaced[COLS.SUGGEST_COHORT_LABEL].unique()) == sorted(
            [
                COHORTS.CLOSED_REP_SAME_SIREN.label,
                COHORTS.CLOSED_REP_OTHER_SIREN.label,
            ]
        )

    @pytest.fixture
    def df_replaced_meme_siret(self, df_replaced):
        return df_replaced[
            df_replaced[COLS.SUGGEST_COHORT_LABEL]
            == COHORTS.CLOSED_REP_SAME_SIREN.label
        ]

    @pytest.fixture
    def df_replaced_autre_siret(self, df_replaced):
        return df_replaced[
            df_replaced[COLS.SUGGEST_COHORT_LABEL]
            == COHORTS.CLOSED_REP_OTHER_SIREN.label
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
        from data.models import Suggestion, SuggestionCohorte
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

        a02 = RevisionActeur.objects.get(pk="a02")
        assert a02.statut == ActeurStatus.INACTIF
        assert a02.parent is None
        assert a02.parent_reason == ""
        assert a02.siret_is_closed is True

    def test_cohorte_meme_siren(self, acteurs, atype, source, df_replaced_meme_siret):
        from data.models import Suggestion, SuggestionCohorte
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

        # Verify changes
        # 1 parent should be created in revision with replacement data
        # 1 child should be created in revision with status=INACT and parent_id pointing
        parent_id = parent_id_generate(["11111111100002"])
        parent = RevisionActeur.objects.get(pk=parent_id)
        assert parent.pk == parent_id
        assert parent.nom == "APRES a1"
        assert parent.adresse == "Adresse1"
        assert parent.code_postal == "12345"
        assert parent.ville == "Ville1"
        assert parent.naf_principal == "naf1"
        assert parent.acteur_type == atype
        assert parent.source is None

        child = RevisionActeur.objects.get(pk="a1")
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent == parent
        assert child.parent_reason == (
            f"SIRET 11111111100001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 11111111100002"
        )
        assert child.siret_is_closed is True

    def test_cohorte_autre_siren(self, acteurs, df_replaced_autre_siret):
        from data.models import Suggestion, SuggestionCohorte
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
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent == parent
        assert child.parent_reason == (
            f"SIRET 22222222200001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 33333333300001"
        )
        assert child.siret_is_closed is True

        parent_id = parent_id_generate(["55555555500001"])
        parent = RevisionActeur.objects.get(pk=parent_id)
        assert parent.nom == "APRES a3"
        assert parent.adresse == "Adresse3"
        assert parent.code_postal == "12345"
        assert parent.ville == "Ville3"
        assert parent.naf_principal == "naf3"

        child = RevisionActeur.objects.get(pk="a3")
        assert child.statut == ActeurStatus.INACTIF
        assert child.parent == parent
        assert child.parent_reason == (
            f"SIRET 44444444400001 détecté le {TODAY} comme fermé dans AE, "
            f"remplacé par SIRET 55555555500001"
        )

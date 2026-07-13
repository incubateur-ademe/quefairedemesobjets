import pandas as pd
import pytest

from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_lien_succession_suggest import (
    GROUP_KEYS,
    _filter_acteurs_a_mettre_a_jour,
    enrich_lien_succession_to_suggestion_groupes,
)


class TestEnrichLienSuccessionSuggest:
    def test_grouping_by_source_and_target_couples(self):
        df = pd.DataFrame(
            [
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-a",
                    COLS.SIREN_ACTUEL: "123456789",
                    COLS.SIRET_ACTUEL: "12345678900001",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-b",
                    COLS.SIREN_ACTUEL: "123456789",
                    COLS.SIRET_ACTUEL: "12345678900001",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-c",
                    COLS.SIREN_ACTUEL: "111111111",
                    COLS.SIRET_ACTUEL: "11111111100001",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
            ]
        )

        grouped = list(df.groupby(GROUP_KEYS, dropna=False))
        assert len(grouped) == 2
        group_sizes = sorted(len(group_df) for _, group_df in grouped)
        assert group_sizes == [1, 2]

    def test_filter_excludes_acteurs_deja_a_jour(self):
        df = pd.DataFrame(
            [
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-a",
                    COLS.SIREN_ACTUEL: "123456789",
                    COLS.SIRET_ACTUEL: "12345678900001",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-b",
                    COLS.SIREN_ACTUEL: "987654321",
                    COLS.SIRET_ACTUEL: "98765432100009",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
            ]
        )

        filtered = _filter_acteurs_a_mettre_a_jour(df)
        assert len(filtered) == 1
        assert filtered.iloc[0][COLS.IDENTIFIANT_UNIQUE] == "acteur-a"

    def test_dry_run_does_not_write(self, mocker):
        df = pd.DataFrame(
            [
                {
                    COLS.IDENTIFIANT_UNIQUE: "acteur-a",
                    COLS.SIREN_ACTUEL: "123456789",
                    COLS.SIRET_ACTUEL: "12345678900001",
                    COLS.SIREN_SUCCESSEUR: "987654321",
                    COLS.SIRET_SUCCESSEUR: "98765432100009",
                },
            ]
        )

        mocker.patch(
            "enrich.tasks.business_logic.enrich_lien_succession_suggest.django_setup_full"
        )
        mocker.patch(
            "enrich.tasks.business_logic.enrich_lien_succession_suggest._est_parent_par_acteur",
            return_value={"acteur-a": False},
        )

        assert (
            enrich_lien_succession_to_suggestion_groupes(
                df=df,
                cohort="cohorte-test",
                suggest_action="ENRICH_ACTEURS_LIEN_SUCCESSION",
                identifiant_action="enrich_siret_siren_lien_succession",
                dry_run=True,
            )
            is False
        )

    def test_raises_on_empty_dataframe(self):
        with pytest.raises(ValueError, match="df vide"):
            enrich_lien_succession_to_suggestion_groupes(
                df=pd.DataFrame(),
                cohort="cohorte-test",
                suggest_action="ENRICH_ACTEURS_LIEN_SUCCESSION",
                identifiant_action="enrich_siret_siren_lien_succession",
                dry_run=True,
            )

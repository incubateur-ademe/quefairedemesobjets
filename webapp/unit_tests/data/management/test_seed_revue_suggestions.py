import pytest
from data.models.suggestion import (
    SOURCE_TYPE_ACTIONS,
    SuggestionAction,
    SuggestionCohorte,
    SuggestionLog,
    SuggestionUnitaire,
)
from data.models.suggestions.source import SuggestionGroupeTypeSource
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from qfdmo.models.acteur import Acteur, RevisionActeur


def nb_lignes(cohorte):
    return (
        SuggestionUnitaire.objects.filter(suggestion_groupe__suggestion_cohorte=cohorte)
        .values("suggestion_groupe_id", "champs")
        .distinct()
        .count()
    )


@pytest.mark.django_db
class TestSeedRevueSuggestions:
    def test_seed_creates_source_cohortes(self):
        call_command("seed_revue_suggestions")

        cohortes = {
            cohorte.type_action: cohorte
            for cohorte in SuggestionCohorte.objects.filter(
                type_action__in=SOURCE_TYPE_ACTIONS,
                identifiant_action__startswith="seed_revue_",
            )
        }
        assert set(cohortes) == {
            SuggestionAction.SOURCE_AJOUT,
            SuggestionAction.SOURCE_MODIFICATION,
            SuggestionAction.SOURCE_SUPPRESSION,
        }
        modification = cohortes[SuggestionAction.SOURCE_MODIFICATION]
        assert modification.suggestion_groupes.count() > 100
        assert nb_lignes(modification) > 500
        assert set(
            SuggestionLog.objects.filter(suggestion_cohorte=modification).values_list(
                "niveau_de_log", flat=True
            )
        ) == {"INFO", "WARNING", "ERROR"}
        assert modification.suggestion_groupes.filter(
            parent_revision_acteur__isnull=False
        ).exists()

    def test_seeded_groupes_are_readable_by_the_source_model(self):
        call_command("seed_revue_suggestions")

        for cohorte in SuggestionCohorte.objects.filter(
            identifiant_action__startswith="seed_revue_"
        ):
            for groupe in cohorte.suggestion_groupes.all():
                SuggestionGroupeTypeSource.from_suggestion_groupe(
                    groupe
                ).to_comparison_table()

    def test_seed_is_idempotent_and_resettable(self):
        call_command("seed_revue_suggestions")
        call_command("seed_revue_suggestions")
        assert (
            SuggestionCohorte.objects.filter(
                identifiant_action__startswith="seed_revue_"
            ).count()
            == 3
        )

        call_command("seed_revue_suggestions", "--reset")
        assert not SuggestionCohorte.objects.filter(
            identifiant_action__startswith="seed_revue_"
        ).exists()
        assert not Acteur.objects.filter(
            identifiant_unique__startswith="seed_revue_"
        ).exists()
        assert not RevisionActeur.objects.filter(
            identifiant_unique__startswith="seed_revue_"
        ).exists()


class TestSeedGuard:
    @pytest.mark.parametrize("environment", ["production", "staging", "preprod"])
    def test_refused_on_real_environments(self, settings, environment):
        settings.ENVIRONMENT = environment

        with pytest.raises(CommandError, match="interdit"):
            call_command("seed_revue_suggestions")

    @pytest.mark.parametrize("database_name", ["webapp", "qfdmo"])
    def test_refused_outside_test_databases(self, monkeypatch, database_name):
        monkeypatch.setitem(connection.settings_dict, "NAME", database_name)

        with pytest.raises(CommandError, match="réservé aux tests"):
            call_command("seed_revue_suggestions")

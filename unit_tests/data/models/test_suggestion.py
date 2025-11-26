import pytest
from django.contrib.gis.geos import Point

from data.models.suggestion import SuggestionAction, SuggestionCohorte, SuggestionGroupe
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


class TestSuggestionCohorte:
    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.SOURCE_AJOUT, True),
            (SuggestionAction.SOURCE_MODIFICATION, True),
            (SuggestionAction.SOURCE_SUPPRESSION, True),
            (SuggestionAction.CLUSTERING, False),
            ("other_action", False),
        ],
    )
    def test_is_source_type(self, type_action, expected_result):
        instance = SuggestionCohorte(type_action=type_action)

        assert instance.is_source_type is expected_result

    @pytest.mark.parametrize(
        "type_action, expected_result",
        [
            (SuggestionAction.CLUSTERING, True),
            (SuggestionAction.SOURCE_AJOUT, False),
            (SuggestionAction.SOURCE_MODIFICATION, False),
            (SuggestionAction.SOURCE_SUPPRESSION, False),
            ("other_action", False),
        ],
    )
    def test_is_clustering_type(self, type_action, expected_result):
        instance = SuggestionCohorte(type_action=type_action)

        assert instance.is_clustering_type is expected_result

    def test_execution_datetime_formats_iso_datetime_in_identifiant_execution(self):
        instance = SuggestionCohorte(
            identifiant_execution="run_2025-01-02T03:04:05_extra"
        )

        assert instance.execution_datetime == "02/01/2025 03:04"

    def test_execution_datetime_returns_original_when_no_datetime_found(self):
        instance = SuggestionCohorte(identifiant_execution="no_date_here")

        assert instance.execution_datetime == "no_date_here"

    def test_str_includes_id_action_and_formatted_execution_datetime(self):
        instance = SuggestionCohorte(
            identifiant_action="my_action",
            identifiant_execution="run_2025-01-02T03:04:05_extra",
        )
        # Simule un objet sauvegardé avec un id
        instance.id = 1

        assert str(instance) == "1 - my_action -- 02/01/2025 03:04"


@pytest.mark.django_db
class TestSuggestionGroupe:
    def test_str_without_acteur_returns_identifiant_action(self):
        cohorte = SuggestionCohorteFactory(identifiant_action="my_action")
        groupe = SuggestionGroupe(suggestion_cohorte=cohorte)

        assert str(groupe) == "my_action"

    def test_str_with_acteur_appends_identifiant_unique(self):
        cohorte = SuggestionCohorteFactory(identifiant_action="my_action")
        acteur = ActeurFactory(identifiant_unique="ID123")
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte, acteur=acteur)

        assert str(groupe) == "my_action - ID123"

    def test_get_suggestion_unitaires_by_champs_groups_by_fields(self):
        groupe = SuggestionGroupeFactory()

        # Deux suggestions avec les mêmes champs mais dans un ordre différent
        su1 = SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            champs=["nom", "ville"],
        )
        su2 = SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            champs=["ville", "nom"],
        )

        # Une suggestion avec des champs différents
        su3 = SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            champs=["code_postal"],
        )

        result = groupe.get_suggestion_unitaires_by_champs()

        # Les deux premières doivent être regroupées ensemble
        assert set(result[(("nom", "ville"))]) == {su1, su2}
        # La troisième dans un groupe séparé
        assert result[(("code_postal",))] == [su3]


@pytest.mark.django_db
class TestSuggestionGroupeSerialiser:
    @pytest.fixture
    def suggestion_groupe_ajout(self):
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["latitude", "longitude"],
            valeurs=[48.56789, 2.56789],
        )
        return suggestion_groupe

    @pytest.fixture
    def suggestion_groupe_modification(self, suggestion_groupe_ajout):
        suggestion_groupe_ajout.suggestion_cohorte.type_action = (
            SuggestionAction.SOURCE_MODIFICATION
        )
        suggestion_groupe_ajout.suggestion_cohorte.save()
        suggestion_groupe_ajout.acteur = ActeurFactory(
            nom="Ancien nom", location=Point(2.1234, 48.1234)
        )
        suggestion_groupe_ajout.save()
        return suggestion_groupe_ajout

    @pytest.mark.django_db
    def test_serialize_source_ajout(self, suggestion_groupe_ajout):

        result = suggestion_groupe_ajout.serialize()

        assert result.id == suggestion_groupe_ajout.id
        assert result.suggestion_cohorte == suggestion_groupe_ajout.suggestion_cohorte
        assert result.action == SuggestionAction.SOURCE_AJOUT
        assert result.old_values == {}
        assert result.new_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.displayed_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.acteur is None
        assert result.acteur_overridden_by is None

    def test_serialize_source_modification_with_acteur(
        self,
        suggestion_groupe_modification,
    ):
        result = suggestion_groupe_modification.serialize()

        assert result.id == suggestion_groupe_modification.id
        assert (
            result.suggestion_cohorte
            == suggestion_groupe_modification.suggestion_cohorte
        )
        assert result.action == SuggestionAction.SOURCE_MODIFICATION
        assert result.old_values == {
            ("nom",): ["Ancien nom"],
            ("latitude", "longitude"): ["48.1234", "2.1234"],
        }
        assert result.new_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.displayed_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.acteur == suggestion_groupe_modification.acteur
        assert result.acteur_overridden_by is None

    def test_serialize_source_modification_with_revisionacteur(
        self,
        suggestion_groupe_modification,
    ):
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()
        result = suggestion_groupe_modification.serialize()

        assert result.id == suggestion_groupe_modification.id
        assert (
            result.suggestion_cohorte
            == suggestion_groupe_modification.suggestion_cohorte
        )
        assert result.action == SuggestionAction.SOURCE_MODIFICATION
        assert result.old_values == {
            ("nom",): ["Ancien nom"],
            ("latitude", "longitude"): ["48.1234", "2.1234"],
        }
        assert result.new_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.displayed_values == {
            ("nom",): ["Revision nom"],
            ("latitude", "longitude"): ["48.01", "2.01"],
        }
        assert result.acteur == suggestion_groupe_modification.acteur
        assert result.acteur_overridden_by == revision_acteur

    def test_serialize_source_modification_with_revisionacteurparent(
        self,
        suggestion_groupe_modification,
    ):
        revision_acteur_parent = RevisionActeurFactory(
            nom="Parent nom",
            location=Point(2.1111, 48.1111),
        )
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
            parent=revision_acteur_parent,
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()
        result = suggestion_groupe_modification.serialize()

        assert result.id == suggestion_groupe_modification.id
        assert (
            result.suggestion_cohorte
            == suggestion_groupe_modification.suggestion_cohorte
        )
        assert result.action == SuggestionAction.SOURCE_MODIFICATION
        assert result.old_values == {
            ("nom",): ["Ancien nom"],
            ("latitude", "longitude"): ["48.1234", "2.1234"],
        }
        assert result.new_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.displayed_values == {
            ("nom",): ["Parent nom"],
            ("latitude", "longitude"): ["48.1111", "2.1111"],
        }
        assert result.acteur == suggestion_groupe_modification.acteur
        assert result.acteur_overridden_by == revision_acteur_parent

    def test_serialize_source_modification_with_revisionacteurparent_parentsuggestion(
        self,
        suggestion_groupe_modification,
    ):
        revision_acteur_parent = RevisionActeurFactory(
            nom="Parent nom",
            location=Point(2.1111, 48.1111),
        )
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
            parent=revision_acteur_parent,
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Suggestion nom"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="RevisionActeur",
            champs=["latitude", "longitude"],
            valeurs=["48.2222", "2.2222"],
        )
        result = suggestion_groupe_modification.serialize()

        assert result.id == suggestion_groupe_modification.id
        assert (
            result.suggestion_cohorte
            == suggestion_groupe_modification.suggestion_cohorte
        )
        assert result.action == SuggestionAction.SOURCE_MODIFICATION
        assert result.old_values == {
            ("nom",): ["Ancien nom"],
            ("latitude", "longitude"): ["48.1234", "2.1234"],
        }
        assert result.new_values == {
            ("nom",): ["Nouveau nom"],
            ("latitude", "longitude"): ["48.56789", "2.56789"],
        }
        assert result.displayed_values == {
            ("nom",): ["Suggestion nom"],
            ("latitude", "longitude"): ["48.2222", "2.2222"],
        }
        assert result.acteur == suggestion_groupe_modification.acteur
        assert result.acteur_overridden_by == revision_acteur_parent

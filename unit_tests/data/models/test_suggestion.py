import pytest

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


@pytest.mark.django_db
class TestSuggestionGroupeSuggestionActeurHasParent:
    def test_suggestion_acteur_has_parent_returns_false_when_no_revision_acteur(self):
        """
        Test that suggestion_acteur_has_parent returns False
        when revision_acteur_id is None
        """
        acteur = ActeurFactory()
        groupe = SuggestionGroupeFactory(acteur=acteur)

        assert groupe.suggestion_acteur_has_parent() is False

    def test_suggestion_acteur_has_parent_returns_false_when_same_ids(self):
        """
        Test that suggestion_acteur_has_parent returns False
        when acteur_id == revision_acteur_id
        """
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Verify that the IDs are different
        assert groupe.acteur_id == groupe.revision_acteur_id
        assert groupe.suggestion_acteur_has_parent() is False

    def test_suggestion_acteur_has_parent_returns_true_when_different_ids(self):
        """
        Test that suggestion_acteur_has_parent returns True
        when acteur_id != revision_acteur_id
        """
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory()
        groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Verify that the IDs are different
        assert groupe.acteur_id != groupe.revision_acteur_id
        assert groupe.suggestion_acteur_has_parent() is True


@pytest.mark.django_db
class TestSuggestionGroupeSuggestionActeurHasRevision:
    def test_suggestion_acteur_has_revision_returns_false_when_no_revision_acteur(self):
        """
        Test that suggestion_acteur_has_revision returns False
        when revision_acteur_id is None
        """
        acteur = ActeurFactory()
        groupe = SuggestionGroupeFactory(acteur=acteur)

        assert groupe.suggestion_acteur_has_revision() is False

    def test_suggestion_acteur_has_revision_returns_true_when_same_ids(self):
        """
        Test that suggestion_acteur_has_revision returns True
        when acteur_id == revision_acteur_id
        """
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Verify that the IDs are different
        assert groupe.acteur_id == groupe.revision_acteur_id
        assert groupe.suggestion_acteur_has_revision() is True

    def test_suggestion_acteur_has_revision_returns_false_when_different_ids(self):
        """
        Test that suggestion_acteur_has_revision returns False
        when acteur_id != revision_acteur_id
        """
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory()
        groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Verify that the IDs are different
        assert groupe.acteur_id != groupe.revision_acteur_id
        assert groupe.suggestion_acteur_has_revision() is False


@pytest.mark.django_db
class TestSuggestionGroupeApply:
    @pytest.fixture
    def suggestion_groupe_source_ajout(self):
        """Fixture for a SuggestionGroupe with type_action SOURCE_AJOUT"""
        from unit_tests.qfdmo.acteur_factory import ActeurTypeFactory, SourceFactory

        # Use a digital acteur_type to avoid the need for location
        ActeurTypeFactory(code="acteur_digital")
        SourceFactory()
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom", "identifiant_unique"],
            valeurs=["Nouveau Acteur", "test_acteur_001"],
        )
        return suggestion_groupe

    @pytest.fixture
    def suggestion_groupe_source_modification(self):
        """Fixture pour un SuggestionGroupe avec type_action SOURCE_MODIFICATION"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="75001")
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom", "code_postal"],
            valeurs=["Nouveau nom", "75002"],
            acteur=acteur,
        )
        return suggestion_groupe

    @pytest.fixture
    def suggestion_groupe_source_modification_with_revision(self):
        """Fixture pour un SuggestionGroupe avec Acteur et RevisionActeur"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="75001")
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique, nom="Revision nom"
        )
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=acteur,
            revision_acteur=revision_acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom Acteur"],
            acteur=acteur,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Nouveau nom Revision"],
            revision_acteur=revision_acteur,
        )
        return suggestion_groupe

    def test_apply_raises_error_when_no_acteur_suggestion_unitaires(self):
        """
        Test that apply() raises an error if there are no Acteur suggestion unitaires
        """
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        # No SuggestionUnitary with suggestion_modele="Acteur"

        with pytest.raises(ValueError, match="No acteur suggestion unitaires found"):
            suggestion_groupe.apply()

    def test_apply_source_modification_with_revision_creates_revision(
        self, suggestion_groupe_source_modification_with_revision
    ):
        """Test that apply() creates/updates a RevisionActeur for SOURCE_MODIFICATION"""
        acteur = suggestion_groupe_source_modification_with_revision.acteur
        revision_acteur = (
            suggestion_groupe_source_modification_with_revision.revision_acteur
        )

        assert acteur.nom == "Ancien nom"
        assert revision_acteur.nom == "Revision nom"

        suggestion_groupe_source_modification_with_revision.apply()

        # Verify that the Acteur has been updated
        acteur.refresh_from_db()
        assert acteur.nom == "Nouveau nom Acteur"

        # Verify that the RevisionActeur has been updated
        revision_acteur.refresh_from_db()
        assert revision_acteur.nom == "Nouveau nom Revision"

    def test_apply_returns_empty_list_for_non_source_actions(self):
        """Test that apply() does nothing for actions that are not SOURCE_*"""
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.CLUSTERING,
            ),
        )

        # apply() should not raise an error but do nothing
        # because _get_apply_models() returns an empty list
        apply_models = suggestion_groupe._get_apply_models()
        assert apply_models == []

        # apply() should not raise an error but do nothing
        suggestion_groupe.apply()

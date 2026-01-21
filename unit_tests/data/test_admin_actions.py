import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from data.admin import (
    SuggestionGroupeAdmin,
    apply_suggestions_to_parent,
    apply_suggestions_to_revision,
)
from data.models.suggestion import SuggestionGroupe
from unit_tests.data.models.suggestion_factory import (
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


@pytest.fixture
def admin_instance():
    """Create a SuggestionGroupeAdmin instance"""
    site = AdminSite()
    return SuggestionGroupeAdmin(SuggestionGroupeFactory._meta.model, site)


@pytest.fixture
def request_factory():
    """Factory to create HTTP requests"""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Create a HTTP request mock with message support"""
    request = request_factory.get("/admin/")
    request.user = AnonymousUser()
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.mark.django_db
class TestApplySuggestionsToParent:
    """Tests apply_suggestions_to_parent from data admin suggestion groupe"""

    def test_apply_suggestions_to_parent_creates_revision_suggestions(
        self, admin_instance, mock_request
    ):
        """Test that the Acteur suggestions are copied to RevisionActeur"""
        # Create an acteur and a revision_acteur parent different
        acteur = ActeurFactory()
        revision_acteur_parent = RevisionActeurFactory()

        # Create a SuggestionGroupe with parent
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur_parent,
        )

        # Create SuggestionUnitaire for Acteur
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
            valeurs=["48.56789", "2.56789"],
        )

        # Verify that there is no SuggestionUnitaire RevisionActeur before
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        # Verify that the SuggestionUnitaire RevisionActeur have been created
        revision_suggestions = suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        )
        assert revision_suggestions.count() == 2

        # Verify the suggestion for "nom"
        su_nom_revision = revision_suggestions.filter(champs=["nom"]).first()
        assert su_nom_revision is not None
        assert su_nom_revision.valeurs == ["Nouveau nom"]
        assert su_nom_revision.revision_acteur == revision_acteur_parent
        assert su_nom_revision.suggestion_modele == "RevisionActeur"

        # Verify the suggestion for "latitude", "longitude"
        su_location_revision = revision_suggestions.filter(
            champs=["latitude", "longitude"]
        ).first()
        assert su_location_revision is not None
        assert su_location_revision.valeurs == ["48.56789", "2.56789"]
        assert su_location_revision.revision_acteur == revision_acteur_parent
        assert su_location_revision.suggestion_modele == "RevisionActeur"

    def test_apply_suggestions_to_parent_updates_existing_revision_suggestions(
        self, admin_instance, mock_request
    ):
        """Test that the existing RevisionActeur suggestions are updated"""
        # Create an acteur and a revision_acteur parent different
        acteur = ActeurFactory()
        revision_acteur_parent = RevisionActeurFactory()

        # Create a SuggestionGroupe with parent
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur_parent,
        )

        # Create a SuggestionUnitaire for Acteur
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Create a SuggestionUnitaire RevisionActeur existing with a different value
        su_revision_existante = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur=revision_acteur_parent,
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        # Verify that the existing suggestion has been updated
        su_revision_existante.refresh_from_db()
        assert su_revision_existante.valeurs == ["Nouveau nom"]
        assert su_revision_existante.revision_acteur == revision_acteur_parent

        # Check that there is only one RevisionActeur suggestion
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["nom"]
            ).count()
            == 1
        )

    def test_apply_suggestions_to_parent_skips_when_no_parent(
        self, admin_instance, mock_request
    ):
        """Test that the action does nothing when there is no parent"""
        # Create a SuggestionGroupe without parent (revision_acteur_id is None)
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            revision_acteur=None,
        )

        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        # Verify that no RevisionActeur suggestion has been created
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

    def test_apply_suggestions_to_parent_skips_when_acteur_equals_revision(
        self, admin_instance, mock_request
    ):
        """Test that the action does nothing when acteur_id == revision_acteur_id"""

        # Créer un acteur et un revision_acteur
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()

        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        # Verify that no RevisionActeur suggestion has been created
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

    def test_apply_suggestions_to_parent_multiple_suggestion_groupes(
        self, admin_instance, mock_request
    ):
        """Test that the action works with multiple SuggestionGroupe"""
        # Create two Acteurs and two RevisionActeur parents
        acteur1 = ActeurFactory()
        revision_acteur_parent1 = RevisionActeurFactory()
        acteur2 = ActeurFactory()
        revision_acteur_parent2 = RevisionActeurFactory()

        # Créer deux SuggestionGroupe avec parent
        sg1 = SuggestionGroupeFactory(
            acteur=acteur1,
            revision_acteur=revision_acteur_parent1,
        )
        sg2 = SuggestionGroupeFactory(
            acteur=acteur2,
            revision_acteur=revision_acteur_parent2,
        )

        # Create SuggestionUnitaire for each group
        SuggestionUnitaireFactory(
            suggestion_groupe=sg1,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 1"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=sg2,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nom 2"],
        )

        # Call the action with the two groups
        queryset = SuggestionGroupe.objects.filter(id__in=[sg1.id, sg2.id])
        apply_suggestions_to_parent(admin_instance, mock_request, queryset)

        # Verify that the suggestions have been created for the two groups
        assert (
            sg1.suggestion_unitaires.filter(suggestion_modele="RevisionActeur").count()
            == 1
        )
        assert (
            sg2.suggestion_unitaires.filter(suggestion_modele="RevisionActeur").count()
            == 1
        )


@pytest.mark.django_db
class TestApplySuggestionsToRevision:
    """Tests action apply_suggestions_to_revision from data admin suggestion_groupe"""

    def test_apply_suggestions_to_revision_creates_revision_suggestions(
        self, admin_instance, mock_request
    ):
        """
        Test that the Acteur suggestions are copied to RevisionActeur when
        acteur_id == revision_acteur_id
        """
        # Create an acteur and a revision_acteur with the same identifiant_unique
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()

        # Create a SuggestionGroupe with revision
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Create a SuggestionUnitaire for Acteur
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Verify that there is no SuggestionUnitaire RevisionActeur before
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_revision(admin_instance, mock_request, queryset)

        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 1
        )
        su_revision = suggestion_groupe.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()
        assert su_revision is not None
        assert su_revision.valeurs == ["Nouveau nom"]
        assert su_revision.revision_acteur == revision_acteur

    def test_apply_suggestions_to_revision_updates_existing_revision_suggestions(
        self, admin_instance, mock_request
    ):
        """Test that the existing RevisionActeur suggestions are updated"""
        # Create an acteur and a revision_acteur
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()

        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur,
        )

        # Create a SuggestionUnitaire for Acteur
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Create a SuggestionUnitaire RevisionActeur existing
        su_revision_existante = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="RevisionActeur",
            revision_acteur=revision_acteur,
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_revision(admin_instance, mock_request, queryset)

        # Verify that the existing suggestion has been updated
        su_revision_existante.refresh_from_db()

        assert su_revision_existante.valeurs == ["Nouveau nom"]

    def test_apply_suggestions_to_revision_skips_when_no_revision(
        self, admin_instance, mock_request
    ):
        """Test that the action does nothing when there is no revision_acteur"""
        suggestion_groupe = SuggestionGroupeFactory(
            acteur=ActeurFactory(),
            revision_acteur=None,
        )

        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_revision(admin_instance, mock_request, queryset)

        # Verify that no RevisionActeur suggestion has been created
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

    def test_apply_suggestions_to_revision_skips_with_parent(
        self, admin_instance, mock_request
    ):
        """
        Test that the action does nothing when revision_acteur_id is different than
        acteur_id (parent case)
        """
        # Create an acteur and a revision_acteur parent different
        acteur = ActeurFactory()
        revision_acteur_parent = RevisionActeurFactory()

        suggestion_groupe = SuggestionGroupeFactory(
            acteur=acteur,
            revision_acteur=revision_acteur_parent,
        )

        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        # Call the action
        queryset = suggestion_groupe._meta.model.objects.filter(id=suggestion_groupe.id)
        apply_suggestions_to_revision(admin_instance, mock_request, queryset)

        # Verify that no RevisionActeur suggestion has been created
        assert (
            suggestion_groupe.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur"
            ).count()
            == 0
        )

from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point

from data.models.apply_models.source_apply_model import SourceApplyModel
from qfdmo.models.acteur import Acteur, RevisionActeur
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    RevisionActeurFactory,
    SourceFactory,
)


@pytest.mark.django_db
class TestSourceApplyModel:
    def test_model_name(self):
        """Test the model name"""
        assert SourceApplyModel.name() == "SourceApplyModel"

    def test_validate_creates_new_acteur(self):
        """Test that validate() creates a new acteur if it doesn't exist,
        don't raise because their isn't any error
        And don't save it in the database"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        apply_model = SourceApplyModel(
            identifiant_unique="test_unique_id",
            data={
                "nom": "Test Acteur",
                "identifiant_unique": "test_unique_id",
                "acteur_type": acteur_type,
                "source": source,
                "location": Point(1, 1),
            },
        )

        acteur = apply_model.validate()

        assert isinstance(acteur, Acteur)
        assert acteur.nom == "Test Acteur"
        assert acteur.identifiant_unique == "test_unique_id"
        assert acteur.acteur_type == acteur_type
        assert acteur.source == source
        # Acteur is not saved in the database
        assert not Acteur.objects.filter(identifiant_unique="test_unique_id").exists()

    def test_validate_updates_existing_acteur(self):
        """Test that validate() updates an existing acteur,
        don't raise because their isn't any error
        And don't save it in the database"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="12345")

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={
                "nom": "Nouveau nom",
                "code_postal": "54321",
            },
        )

        validated_acteur = apply_model.validate()

        assert validated_acteur.nom == "Nouveau nom"
        assert validated_acteur.code_postal == "54321"
        # L'acteur en base n'est pas encore modifié
        acteur.refresh_from_db()
        assert acteur.nom == "Ancien nom"
        assert acteur.code_postal == "12345"

    def test_validate_raises_validation_error_on_invalid_data(self):
        """Test that validate() raises a ValidationError if the data is invalid"""
        apply_model = SourceApplyModel(
            identifiant_unique="test_invalid",
            data={
                "nom": "",  # nom ne peut pas être vide
            },
        )

        with pytest.raises(Exception):  # Django ValidationError
            apply_model.validate()

    @patch.object(SourceApplyModel, "validate")
    def test_validate_is_called_by_apply(self, mock_validate):
        """Test that apply() calls validate()"""
        acteur = ActeurFactory()
        mock_validate.return_value = acteur

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"nom": "Nouveau nom"},
        )

        apply_model.apply()

        mock_validate.assert_called_once()

    def test_apply_creates_new_acteur(self):
        """Test that apply() creates and saves a new acteur"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        apply_model = SourceApplyModel(
            identifiant_unique="new_acteur_id",
            data={
                "nom": "Nouvel Acteur",
                "identifiant_unique": "new_acteur_id",
                "acteur_type": acteur_type,
                "source": source,
                "location": Point(1, 1),
            },
        )

        apply_model.apply()

        acteur = Acteur.objects.get(identifiant_unique="new_acteur_id")
        assert acteur.nom == "Nouvel Acteur"
        assert acteur.acteur_type == acteur_type
        assert acteur.source == source

    def test_apply_updates_existing_acteur(self):
        """Test that apply() updates and saves an existing acteur"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="12345")

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={
                "nom": "Nouveau nom",
                "code_postal": "54321",
            },
        )

        apply_model.apply()

        acteur.refresh_from_db()
        assert acteur.nom == "Nouveau nom"
        assert acteur.code_postal == "54321"

    def test_validate_with_revision_acteur_model(self):
        """Test that validate() works with RevisionActeur as model"""
        revision_acteur = RevisionActeurFactory(nom="Ancien nom")

        apply_model = SourceApplyModel(
            identifiant_unique=revision_acteur.identifiant_unique,
            acteur_model=RevisionActeur,
            data={
                "nom": "Nouveau nom",
            },
        )

        validated = apply_model.validate()

        assert isinstance(validated, RevisionActeur)
        assert validated.nom == "Nouveau nom"
        # La révision en base n'est pas encore modifiée
        revision_acteur.refresh_from_db()
        assert revision_acteur.nom == "Ancien nom"

    def test_apply_with_revision_acteur_model(self):
        """Test that apply() works with RevisionActeur as model"""
        revision_acteur = RevisionActeurFactory(nom="Ancien nom")

        apply_model = SourceApplyModel(
            identifiant_unique=revision_acteur.identifiant_unique,
            acteur_model=RevisionActeur,
            data={
                "nom": "Nouveau nom",
            },
        )

        apply_model.apply()

        revision_acteur.refresh_from_db()
        assert revision_acteur.nom == "Nouveau nom"

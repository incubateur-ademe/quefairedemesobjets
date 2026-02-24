import json
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point

from data.models.apply_models.source_apply_model import SourceApplyModel
from qfdmo.models.acteur import (
    Acteur,
    PerimetreADomicile,
    RevisionActeur,
    RevisionPerimetreADomicile,
    RevisionPropositionService,
)
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurServiceFactory,
    ActeurTypeFactory,
    LabelQualiteFactory,
    PerimetreADomicileFactory,
    PropositionServiceFactory,
    RevisionActeurFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


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

    def test_validate_creates_acteur_with_latitude_longitude(self):
        """Test that validate() converts latitude and longitude to location Point"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        apply_model = SourceApplyModel(
            identifiant_unique="test_latlong_id",
            data={
                "nom": "Test Acteur",
                "identifiant_unique": "test_latlong_id",
                "acteur_type": acteur_type,
                "source": source,
                "latitude": "48.8566",
                "longitude": "2.3522",
            },
        )

        acteur = apply_model.validate()

        assert isinstance(acteur, Acteur)
        assert acteur.location is not None
        assert isinstance(acteur.location, Point)
        assert acteur.location.x == 2.3522  # longitude
        assert acteur.location.y == 48.8566  # latitude
        # Vérifier que data_latlong_to_location convertit correctement
        from data.models.utils import prepare_acteur_data_with_location

        converted_data = prepare_acteur_data_with_location(apply_model.data)
        assert "latitude" not in converted_data
        assert "longitude" not in converted_data
        assert "location" in converted_data

    def test_apply_creates_acteur_with_latitude_longitude(self):
        """
        Test that apply() creates an acteur with latitude/longitude converted to
        location.
        """
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        apply_model = SourceApplyModel(
            identifiant_unique="new_latlong_id",
            data={
                "nom": "Nouvel Acteur",
                "identifiant_unique": "new_latlong_id",
                "acteur_type": acteur_type,
                "source": source,
                "latitude": "45.7640",
                "longitude": "4.8357",
            },
        )

        apply_model.apply()

        acteur = Acteur.objects.get(identifiant_unique="new_latlong_id")
        assert acteur.location is not None
        assert isinstance(acteur.location, Point)
        assert acteur.location.x == 4.8357  # longitude
        assert acteur.location.y == 45.7640  # latitude

    def test_set_foreign_key_from_code_with_foreign_key_codes(self):
        """Test _set_foreign_key_from_code with ForeignKey fields ending with _code"""
        acteur = ActeurFactory()
        new_source = SourceFactory(code="new_source")
        new_acteur_type = ActeurTypeFactory(code="new_type")

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={
                "source_code": new_source.code,
                "acteur_type_code": new_acteur_type.code,
            },
        )

        apply_model._set_foreign_key_from_code(acteur, apply_model.data)

        assert acteur.source == new_source
        assert acteur.acteur_type == new_acteur_type

    def test_set_acteur_linked_objects_with_proposition_service_codes(self):
        """Test _set_acteur_linked_objects with proposition_service_codes for Acteur"""
        acteur = ActeurFactory()
        action1 = ActionFactory(code="action1")
        action2 = ActionFactory(code="action2")
        sous_cat1 = SousCategorieObjetFactory(code="cat1")
        sous_cat2 = SousCategorieObjetFactory(code="cat2")
        sous_cat3 = SousCategorieObjetFactory(code="cat3")

        # Créer des proposition services existantes
        PropositionServiceFactory(acteur=acteur, action=action1)
        assert acteur.proposition_services.count() == 1

        proposition_service_data = json.dumps(
            [
                {
                    "action": action1.code,
                    "sous_categories": [sous_cat1.code, sous_cat2.code],
                },
                {
                    "action": action2.code,
                    "sous_categories": [sous_cat3.code],
                },
            ]
        )

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"proposition_service_codes": proposition_service_data},
        )

        apply_model._set_acteur_linked_objects(acteur, apply_model.data)

        assert acteur.proposition_services.count() == 2
        ps1 = acteur.proposition_services.filter(action=action1).first()
        assert ps1 is not None
        assert ps1.sous_categories.count() == 2
        assert sous_cat1 in ps1.sous_categories.all()
        assert sous_cat2 in ps1.sous_categories.all()

        ps2 = acteur.proposition_services.filter(action=action2).first()
        assert ps2 is not None
        assert ps2.sous_categories.count() == 1
        assert sous_cat3 in ps2.sous_categories.all()

    def test_set_acteur_linked_objects_with_proposition_service_codes_revision(self):
        """
        Test _set_acteur_linked_objects with proposition_service_codes for
        RevisionActeur.
        """
        revision_acteur = RevisionActeurFactory()
        action = ActionFactory(code="action1")
        sous_cat = SousCategorieObjetFactory(code="cat1")

        proposition_service_data = json.dumps(
            [
                {
                    "action": action.code,
                    "sous_categories": [sous_cat.code],
                },
            ]
        )

        apply_model = SourceApplyModel(
            identifiant_unique=revision_acteur.identifiant_unique,
            acteur_model=RevisionActeur,
            data={"proposition_service_codes": proposition_service_data},
        )

        apply_model._set_acteur_linked_objects(revision_acteur, apply_model.data)

        assert revision_acteur.proposition_services.count() == 1
        ps = revision_acteur.proposition_services.first()
        assert isinstance(ps, RevisionPropositionService)
        assert ps.action == action
        assert ps.sous_categories.count() == 1
        assert sous_cat in ps.sous_categories.all()

    def test_set_acteur_linked_objects_with_perimetre_adomicile_codes(self):
        """Test _set_acteur_linked_objects with perimetre_adomicile_codes for Acteur"""
        acteur = ActeurFactory()

        # Créer un périmètre existant
        PerimetreADomicileFactory(
            acteur=acteur,
            type=PerimetreADomicile.Type.KILOMETRIQUE,
            valeur="10",
        )
        assert acteur.perimetre_adomiciles.count() == 1

        perimetre_data = json.dumps(
            [
                {"type": PerimetreADomicile.Type.DEPARTEMENTAL, "valeur": "75"},
                {"type": PerimetreADomicile.Type.KILOMETRIQUE, "valeur": "20"},
            ]
        )

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"perimetre_adomicile_codes": perimetre_data},
        )

        apply_model._set_acteur_linked_objects(acteur, apply_model.data)

        assert acteur.perimetre_adomiciles.count() == 2
        perimetres = list(acteur.perimetre_adomiciles.all())
        types = [p.type for p in perimetres]
        valeurs = [p.valeur for p in perimetres]
        assert PerimetreADomicile.Type.DEPARTEMENTAL in types
        assert PerimetreADomicile.Type.KILOMETRIQUE in types
        assert "75" in valeurs
        assert "20" in valeurs

    def test_set_acteur_linked_objects_with_perimetre_adomicile_codes_revision(self):
        """
        Test _set_acteur_linked_objects with perimetre_adomicile_codes for
        RevisionActeur.
        """
        revision_acteur = RevisionActeurFactory()

        perimetre_data = json.dumps(
            [
                {"type": PerimetreADomicile.Type.FRANCE_METROPOLITAINE, "valeur": ""},
            ]
        )

        apply_model = SourceApplyModel(
            identifiant_unique=revision_acteur.identifiant_unique,
            acteur_model=RevisionActeur,
            data={"perimetre_adomicile_codes": perimetre_data},
        )

        apply_model._set_acteur_linked_objects(revision_acteur, apply_model.data)

        assert revision_acteur.perimetre_adomiciles.count() == 1
        perimetre = revision_acteur.perimetre_adomiciles.first()
        assert isinstance(perimetre, RevisionPerimetreADomicile)
        assert perimetre.type == PerimetreADomicile.Type.FRANCE_METROPOLITAINE

    def test_set_acteur_linked_objects_with_label_codes(self):
        """Test _set_acteur_linked_objects with label_codes (ManyToMany)"""
        acteur = ActeurFactory()
        label1 = LabelQualiteFactory(code="label1")
        label2 = LabelQualiteFactory(code="label2")
        label3 = LabelQualiteFactory(code="label3")

        # Ajouter un label existant
        acteur.labels.add(label1)
        assert acteur.labels.count() == 1

        label_data = json.dumps([label2.code, label3.code])

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"label_codes": label_data},
        )

        apply_model._set_acteur_linked_objects(acteur, apply_model.data)

        assert acteur.labels.count() == 2
        assert label2 in acteur.labels.all()
        assert label3 in acteur.labels.all()
        assert label1 not in acteur.labels.all()  # Ancien label supprimé

    def test_set_acteur_linked_objects_with_empty_label_codes(self):
        """
        Test _set_acteur_linked_objects with empty label_codes list removes all labels
        """
        acteur = ActeurFactory()
        label1 = LabelQualiteFactory(code="label1")
        label2 = LabelQualiteFactory(code="label2")

        # Ajouter des labels existants
        acteur.labels.add(label1, label2)
        assert acteur.labels.count() == 2

        # Appliquer une liste vide de labels
        empty_label_data = json.dumps([])

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"label_codes": empty_label_data},
        )

        apply_model._set_acteur_linked_objects(acteur, apply_model.data)

        # Tous les labels doivent être supprimés
        assert acteur.labels.count() == 0

    def test_apply_with_empty_label_codes(self):
        """Test apply() with empty label_codes removes all labels from acteur"""
        acteur = ActeurFactory()
        label1 = LabelQualiteFactory(code="label1")
        label2 = LabelQualiteFactory(code="label2")

        # Ajouter des labels existants
        acteur.labels.add(label1, label2)
        acteur.save()
        assert acteur.labels.count() == 2

        # Appliquer avec une liste vide de labels
        empty_label_data = json.dumps([])

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"label_codes": empty_label_data},
        )

        apply_model.apply()

        # Vérifier que les labels ont été supprimés après apply()
        acteur.refresh_from_db()
        assert acteur.labels.count() == 0

    def test_set_acteur_linked_objects_with_acteur_service_codes(self):
        """Test _set_acteur_linked_objects with acteur_service_codes (ManyToMany)"""
        acteur = ActeurFactory()
        service1 = ActeurServiceFactory(code="service1")
        service2 = ActeurServiceFactory(code="service2")
        service3 = ActeurServiceFactory(code="service3")

        # Ajouter un service existant
        acteur.acteur_services.add(service1)
        assert acteur.acteur_services.count() == 1

        service_data = json.dumps([service2.code, service3.code])

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"acteur_service_codes": service_data},
        )

        apply_model._set_acteur_linked_objects(acteur, apply_model.data)

        assert acteur.acteur_services.count() == 2
        assert service2 in acteur.acteur_services.all()
        assert service3 in acteur.acteur_services.all()
        assert service1 not in acteur.acteur_services.all()  # Ancien service supprimé

    def test_set_foreign_key_from_code_raises_error_for_non_foreignkey_code(self):
        """
        Test that _set_foreign_key_from_code raises ValueError for non-ForeignKey fields
        """
        acteur = ActeurFactory()

        apply_model = SourceApplyModel(
            identifiant_unique=acteur.identifiant_unique,
            data={"nom_code": "invalid"},  # nom n'est pas une ForeignKey
        )

        with pytest.raises(ValueError, match="Field nom is not a ForeignKey"):
            apply_model._set_foreign_key_from_code(acteur, apply_model.data)

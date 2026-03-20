import json

import pytest
from django.contrib.gis.geos import Point

from data.models.suggestions.source import SuggestionGroupeTypeSource
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
class TestSuggestionGroupeTypeSourceApplyOne:
    def test_creates_new_acteur(self):
        """Test that _apply_one creates a new acteur if it doesn't exist"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        acteur = SuggestionGroupeTypeSource._apply_one(
            Acteur,
            "test_unique_id",
            {
                "nom": "Test Acteur",
                "identifiant_unique": "test_unique_id",
                "acteur_type": acteur_type,
                "source": source,
                "location": Point(1, 1),
            },
        )

        assert isinstance(acteur, Acteur)
        assert acteur.nom == "Test Acteur"
        assert acteur.identifiant_unique == "test_unique_id"
        assert acteur.acteur_type == acteur_type
        assert acteur.source == source
        assert Acteur.objects.filter(identifiant_unique="test_unique_id").exists()

    def test_updates_existing_acteur(self):
        """Test that _apply_one updates an existing acteur"""
        acteur = ActeurFactory(nom="Ancien nom", code_postal="12345")

        result = SuggestionGroupeTypeSource._apply_one(
            Acteur,
            acteur.identifiant_unique,
            {
                "nom": "Nouveau nom",
                "code_postal": "54321",
            },
        )

        assert result.nom == "Nouveau nom"
        assert result.code_postal == "54321"
        acteur.refresh_from_db()
        assert acteur.nom == "Nouveau nom"
        assert acteur.code_postal == "54321"

    def test_raises_validation_error_on_invalid_data(self):
        """Test that _apply_one raises a ValidationError if the data is invalid"""
        with pytest.raises(Exception):
            SuggestionGroupeTypeSource._apply_one(
                Acteur,
                "test_invalid",
                {"nom": ""},
            )

    def test_creates_acteur_with_latitude_longitude(self):
        """Test that _apply_one converts latitude and longitude to location Point"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        acteur = SuggestionGroupeTypeSource._apply_one(
            Acteur,
            "new_latlong_id",
            {
                "nom": "Nouvel Acteur",
                "identifiant_unique": "new_latlong_id",
                "acteur_type": acteur_type,
                "source": source,
                "latitude": "45.7640",
                "longitude": "4.8357",
            },
        )

        assert acteur.location is not None
        assert isinstance(acteur.location, Point)
        assert acteur.location.x == 4.8357
        assert acteur.location.y == 45.7640

    def test_with_revision_acteur_model(self):
        """Test that _apply_one works with RevisionActeur as model"""
        revision_acteur = RevisionActeurFactory(nom="Ancien nom")

        result = SuggestionGroupeTypeSource._apply_one(
            RevisionActeur,
            revision_acteur.identifiant_unique,
            {"nom": "Nouveau nom"},
        )

        assert isinstance(result, RevisionActeur)
        assert result.nom == "Nouveau nom"
        revision_acteur.refresh_from_db()
        assert revision_acteur.nom == "Nouveau nom"


@pytest.mark.django_db
class TestSuggestionGroupeTypeSourceSetForeignKey:
    def test_set_foreign_key_from_code_with_foreign_key_codes(self):
        """Test _set_foreign_key_from_code with ForeignKey fields ending with _code"""
        acteur = ActeurFactory()
        new_source = SourceFactory(code="new_source")
        new_acteur_type = ActeurTypeFactory(code="new_type")

        SuggestionGroupeTypeSource._set_foreign_key_from_code(
            acteur,
            {
                "source_code": new_source.code,
                "acteur_type_code": new_acteur_type.code,
            },
        )

        assert acteur.source == new_source
        assert acteur.acteur_type == new_acteur_type

    def test_set_foreign_key_from_code_raises_error_for_non_foreignkey_code(self):
        """
        Test that _set_foreign_key_from_code raises ValueError for non-ForeignKey fields
        """
        acteur = ActeurFactory()

        with pytest.raises(ValueError, match="Field nom is not a ForeignKey"):
            SuggestionGroupeTypeSource._set_foreign_key_from_code(
                acteur, {"nom_code": "invalid"}
            )


@pytest.mark.django_db
class TestSuggestionGroupeTypeSourceSetLinkedObjects:
    def test_with_proposition_service_codes(self):
        """Test _set_acteur_linked_objects with proposition_service_codes for Acteur"""
        acteur = ActeurFactory()
        action1 = ActionFactory(code="action1")
        action2 = ActionFactory(code="action2")
        sous_cat1 = SousCategorieObjetFactory(code="cat1")
        sous_cat2 = SousCategorieObjetFactory(code="cat2")
        sous_cat3 = SousCategorieObjetFactory(code="cat3")

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

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            acteur, {"proposition_service_codes": proposition_service_data}
        )

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

    def test_with_proposition_service_codes_revision(self):
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

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            revision_acteur, {"proposition_service_codes": proposition_service_data}
        )

        assert revision_acteur.proposition_services.count() == 1
        ps = revision_acteur.proposition_services.first()
        assert isinstance(ps, RevisionPropositionService)
        assert ps.action == action
        assert ps.sous_categories.count() == 1
        assert sous_cat in ps.sous_categories.all()

    def test_with_perimetre_adomicile_codes(self):
        """Test _set_acteur_linked_objects with perimetre_adomicile_codes for Acteur"""
        acteur = ActeurFactory()

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

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            acteur, {"perimetre_adomicile_codes": perimetre_data}
        )

        assert acteur.perimetre_adomiciles.count() == 2
        perimetres = list(acteur.perimetre_adomiciles.all())
        types = [p.type for p in perimetres]
        valeurs = [p.valeur for p in perimetres]
        assert PerimetreADomicile.Type.DEPARTEMENTAL in types
        assert PerimetreADomicile.Type.KILOMETRIQUE in types
        assert "75" in valeurs
        assert "20" in valeurs

    def test_with_perimetre_adomicile_codes_revision(self):
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

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            revision_acteur, {"perimetre_adomicile_codes": perimetre_data}
        )

        assert revision_acteur.perimetre_adomiciles.count() == 1
        perimetre = revision_acteur.perimetre_adomiciles.first()
        assert isinstance(perimetre, RevisionPerimetreADomicile)
        assert perimetre.type == PerimetreADomicile.Type.FRANCE_METROPOLITAINE

    def test_with_label_codes(self):
        """Test _set_acteur_linked_objects with label_codes (ManyToMany)"""
        acteur = ActeurFactory()
        label1 = LabelQualiteFactory(code="label1")
        label2 = LabelQualiteFactory(code="label2")
        label3 = LabelQualiteFactory(code="label3")

        acteur.labels.add(label1)
        assert acteur.labels.count() == 1

        label_data = json.dumps([label2.code, label3.code])

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            acteur, {"label_codes": label_data}
        )

        assert acteur.labels.count() == 2
        assert label2 in acteur.labels.all()
        assert label3 in acteur.labels.all()
        assert label1 not in acteur.labels.all()

    def test_with_empty_label_codes(self):
        """
        Test _set_acteur_linked_objects with empty label_codes list removes all labels
        """
        acteur = ActeurFactory()
        label1 = LabelQualiteFactory(code="label1")
        label2 = LabelQualiteFactory(code="label2")

        acteur.labels.add(label1, label2)
        assert acteur.labels.count() == 2

        empty_label_data = json.dumps([])

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            acteur, {"label_codes": empty_label_data}
        )

        assert acteur.labels.count() == 0

    def test_with_acteur_service_codes(self):
        """Test _set_acteur_linked_objects with acteur_service_codes (ManyToMany)"""
        acteur = ActeurFactory()
        service1 = ActeurServiceFactory(code="service1")
        service2 = ActeurServiceFactory(code="service2")
        service3 = ActeurServiceFactory(code="service3")

        acteur.acteur_services.add(service1)
        assert acteur.acteur_services.count() == 1

        service_data = json.dumps([service2.code, service3.code])

        SuggestionGroupeTypeSource._set_acteur_linked_objects(
            acteur, {"acteur_service_codes": service_data}
        )

        assert acteur.acteur_services.count() == 2
        assert service2 in acteur.acteur_services.all()
        assert service3 in acteur.acteur_services.all()
        assert service1 not in acteur.acteur_services.all()

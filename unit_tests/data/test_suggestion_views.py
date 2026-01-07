import pytest
from django.contrib.gis.geos import Point

from data.models.suggestion import SuggestionAction
from data.views import serialize_suggestion_groupe, update_suggestion_groupe
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


@pytest.mark.django_db
class TestSerializeSuggestionGroupe:
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
        result = serialize_suggestion_groupe(suggestion_groupe_ajout).to_dict()

        expected_result = {
            "id": suggestion_groupe_ajout.id,
            "suggestion_cohorte": suggestion_groupe_ajout.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_AJOUT",
            "identifiant_unique": "",
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "new_value": "Nouveau nom",
                    "updated_displayed_value": "",
                },
                "latitude": {
                    "displayed_value": "48.56789",
                    "new_value": "48.56789",
                    "updated_displayed_value": "",
                },
                "longitude": {
                    "displayed_value": "2.56789",
                    "new_value": "2.56789",
                    "updated_displayed_value": "",
                },
            },
            "acteur": None,
            "acteur_overridden_by": None,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_acteur(
        self,
        suggestion_groupe_modification,
    ):
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.56789",
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.56789",
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": None,
        }

        assert result == expected_result

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
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Revision nom",
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.01",
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.01",
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": revision_acteur,
        }

        assert result == expected_result

    def test_serialize_source_modification_with_revisionacteurparent(
        self,
        suggestion_groupe_modification,
    ):
        revision_acteur_parent = RevisionActeurFactory(
            nom="Parent nom",
            location=Point(2.1111, 48.1111),
        )
        RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
            parent=revision_acteur_parent,
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur_parent
        suggestion_groupe_modification.save()
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Parent nom",
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.1111",
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.1111",
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": revision_acteur_parent,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_revisionacteurparent_parentsuggestion(
        self,
        suggestion_groupe_modification,
    ):
        revision_acteur_parent = RevisionActeurFactory(
            nom="Parent nom",
            location=Point(2.1111, 48.1111),
        )
        RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
            parent=revision_acteur_parent,
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur_parent
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
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Parent nom",
                    "updated_displayed_value": "Suggestion nom",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.1111",
                    "updated_displayed_value": "48.2222",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.1111",
                    "updated_displayed_value": "2.2222",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": revision_acteur_parent,
        }
        assert result == expected_result

    def test_serialize_source_ajout_with_identifiant_unique(self):
        """Test that SOURCE_AJOUT with a non empty identifiant_unique"""
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_AJOUT,
            ),
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["identifiant_unique"],
            valeurs=["ID_UNIQUE_123"],
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        result = serialize_suggestion_groupe(suggestion_groupe).to_dict()

        expected_result = {
            "id": suggestion_groupe.id,
            "suggestion_cohorte": suggestion_groupe.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_AJOUT",
            "identifiant_unique": "ID_UNIQUE_123",
            "fields_groups": [("identifiant_unique",), ("nom",)],
            "fields_values": {
                "identifiant_unique": {
                    "displayed_value": "ID_UNIQUE_123",
                    "new_value": "ID_UNIQUE_123",
                    "updated_displayed_value": "",
                },
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "new_value": "Nouveau nom",
                    "updated_displayed_value": "",
                },
            },
            "acteur": None,
            "acteur_overridden_by": None,
        }
        assert result == expected_result

    def test_serialize_source_ajout_with_revisionacteur_suggestions(self):
        """Test that SOURCE_AJOUT with suggestion_unitaires of type RevisionActeur"""
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
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Revision nom"],
        )
        result = serialize_suggestion_groupe(suggestion_groupe).to_dict()

        expected_result = {
            "id": suggestion_groupe.id,
            "suggestion_cohorte": suggestion_groupe.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_AJOUT",
            "identifiant_unique": "",
            "fields_groups": [("nom",)],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "new_value": "Nouveau nom",
                    "updated_displayed_value": "Revision nom",
                },
            },
            "acteur": None,
            "acteur_overridden_by": None,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_missing_fields_in_suggestions(
        self,
        suggestion_groupe_modification,
    ):
        """
        Test that SOURCE_MODIFICATION with missing fields in acteur_suggestion_unitaires
        """
        # Delete the existing suggestion_unitaires to keep only "nom"
        suggestion_groupe_modification.suggestion_unitaires.exclude(
            champs__contains=["nom"]
        ).delete()
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",)],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": None,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_missing_field_in_acteur_overridden_by(
        self,
        suggestion_groupe_modification,
    ):
        """Test that SOURCE_MODIFICATION with a missing field in acteur_overridden_by"""
        # Create a revision_acteur without location (optional field)
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=None,  # Pas de location dans revision_acteur
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        # When acteur_overridden_by doesn't have a location, we must use
        # acteur_suggestion_unitaires_by_field for latitude/longitude
        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Revision nom",  # From acteur_overridden_by
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.56789",  # Not from acteur_overridden_by
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.56789",  # Not from acteur_overridden_by
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": revision_acteur,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_missing_field_in_acteur(
        self,
        suggestion_groupe_modification,
    ):
        """Test that SOURCE_MODIFICATION with a field that doesn't exist in acteur"""
        # Add a field that doesn't exist in the acteur
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="Acteur",
            champs=["code_postal"],
            valeurs=["75001"],
        )
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        # The code_postal field should use getattr(acteur, field, "") which returns ""
        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("code_postal",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",
                    "updated_displayed_value": "",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.56789",
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.56789",
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
                "code_postal": {
                    "displayed_value": "75001",  # From acteur_suggestion_unitaires
                    "updated_displayed_value": "",
                    "new_value": "75001",
                    "old_value": "",  # getattr(acteur, field, "") returns ""
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": None,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_revisionacteur_but_rev_suggestion(
        self,
        suggestion_groupe_modification,
    ):
        """
        Test that SOURCE_MODIFICATION with a revision_acteur
        but no revision_acteur_suggestion_unitaires
        """
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()
        # No revision_acteur_suggestion_unitaires
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Revision nom",
                    "updated_displayed_value": "",  # No RevisionActeur suggestion
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.01",
                    "updated_displayed_value": "",  # No RevisionActeur suggestion
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.01",
                    "updated_displayed_value": "",  # No RevisionActeur suggestion
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": revision_acteur,
        }
        assert result == expected_result

    def test_serialize_source_modification_with_rev_suggestion_but_no_revisionacteur(
        self,
        suggestion_groupe_modification,
    ):
        """
        Test that SOURCE_MODIFICATION with revision_acteur_suggestion_unitaires
        but no revision_acteur
        """
        # No revision_acteur but with revision_acteur_suggestion_unitaires
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Revision suggestion nom"],
        )
        result = serialize_suggestion_groupe(suggestion_groupe_modification).to_dict()

        # acteur_overridden_by_suggestion_unitaires_by_field should be filled
        expected_result = {
            "id": suggestion_groupe_modification.id,
            "suggestion_cohorte": suggestion_groupe_modification.suggestion_cohorte,
            "statut": "🟠 À valider",
            "action": "SOURCE_MODIFICATION",
            "identifiant_unique": (
                suggestion_groupe_modification.acteur.identifiant_unique
            ),
            "fields_groups": [("nom",), ("latitude", "longitude")],
            "fields_values": {
                "nom": {
                    "displayed_value": "Nouveau nom",  # From suggestion_unitaires
                    "updated_displayed_value": "Revision suggestion nom",
                    "new_value": "Nouveau nom",
                    "old_value": "Ancien nom",
                },
                "latitude": {
                    "displayed_value": "48.56789",
                    "updated_displayed_value": "",
                    "new_value": "48.56789",
                    "old_value": "48.1234",
                },
                "longitude": {
                    "displayed_value": "2.56789",
                    "updated_displayed_value": "",
                    "new_value": "2.56789",
                    "old_value": "2.1234",
                },
            },
            "acteur": suggestion_groupe_modification.acteur,
            "acteur_overridden_by": None,
        }
        assert result == expected_result


@pytest.mark.django_db
class TestUpdateSuggestionGroupe:
    @pytest.fixture
    def suggestion_groupe_with_acteur(self):
        """Fixture to create a SuggestionGroupe with an acteur"""
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=ActeurFactory(nom="Ancien nom", location=Point(2.1234, 48.1234)),
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

    def test_update_from_serialized_data_success_single_field(
        self, suggestion_groupe_with_acteur
    ):
        """Test successful update with a single field"""
        fields_values = {
            "nom": {
                "displayed_value": "Ancien nom",
                "updated_displayed_value": "Nom mis à jour",
                "new_value": "Nouveau nom",
                "old_value": "Ancien nom",
            }
        }
        fields_groups = [("nom",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Vérifier que le SuggestionUnitaire a été créé
        suggestion_unitaire = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.valeurs == ["Nom mis à jour"]

    def test_update_from_serialized_data_success_grouped_fields(
        self, suggestion_groupe_with_acteur
    ):
        """Test successful update with grouped fields (latitude/longitude)"""
        fields_values = {
            "latitude": {
                "displayed_value": "48.1234",
                "updated_displayed_value": "48.9999",
                "new_value": "48.56789",
                "old_value": "48.1234",
            },
            "longitude": {
                "displayed_value": "2.1234",
                "updated_displayed_value": "2.9999",
                "new_value": "2.56789",
                "old_value": "2.1234",
            },
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Vérifier que le SuggestionUnitaire a été créé avec les deux valeurs
        suggestion_unitaire = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
        ).first()
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.valeurs == ["48.9999", "2.9999"]

    def test_update_from_serialized_data_success_multiple_fields(
        self, suggestion_groupe_with_acteur
    ):
        """Test successful update with multiple fields"""
        fields_values = {
            "nom": {
                "displayed_value": "Ancien nom",
                "updated_displayed_value": "Nom mis à jour",
                "new_value": "Nouveau nom",
                "old_value": "Ancien nom",
            },
            "code_postal": {
                "displayed_value": "",
                "updated_displayed_value": "75001",
                "new_value": "",
                "old_value": "",
            },
        }
        fields_groups = [("nom",), ("code_postal",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Vérifier que les deux SuggestionUnitaires ont été créés
        nom_suggestion = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()
        assert nom_suggestion is not None
        assert nom_suggestion.valeurs == ["Nom mis à jour"]

        cp_suggestion = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["code_postal"]
        ).first()
        assert cp_suggestion is not None
        assert cp_suggestion.valeurs == ["75001"]

    def test_update_from_serialized_data_error_invalid_longitude(
        self, suggestion_groupe_with_acteur
    ):
        """Test error when longitude is not a valid float"""
        fields_values = {
            "longitude": {
                "displayed_value": "2.1234",
                "updated_displayed_value": "not_a_float",
                "new_value": "2.56789",
                "old_value": "2.1234",
            },
            "latitude": {
                "displayed_value": "48.1234",
                "updated_displayed_value": "48.9999",
                "new_value": "48.56789",
                "old_value": "48.1234",
            },
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is False
        assert errors is not None
        assert "longitude" in errors
        assert "must be a float" in errors["longitude"]

    def test_update_from_serialized_data_no_update_when_values_equal(
        self, suggestion_groupe_with_acteur
    ):
        """
        Test that no update is created when updated_displayed_value == displayed_value
        """
        fields_values = {
            "nom": {
                "displayed_value": "Ancien nom",
                "updated_displayed_value": "Ancien nom",  # Same as displayed_value
                "new_value": "Nouveau nom",
                "old_value": "Ancien nom",
            }
        }
        fields_groups = [("nom",)]

        initial_count = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).count()

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Verify that no new SuggestionUnitaire has been created
        final_count = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).count()
        assert final_count == initial_count

    def test_update_from_serialized_data_update_existing_revision_suggestion(
        self, suggestion_groupe_with_acteur
    ):
        """
        Test update when a RevisionActeur suggestion already exists with different value
        """
        # Create a RevisionActeur suggestion
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_with_acteur,
            suggestion_modele="RevisionActeur",
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        fields_values = {
            "nom": {
                "displayed_value": "Ancien nom",
                "updated_displayed_value": "Nouvelle valeur",
                "new_value": "Nouveau nom",
                "old_value": "Ancien nom",
            }
        }
        fields_groups = [("nom",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Verify that the SuggestionUnitaire has been updated
        suggestion_unitaire = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.valeurs == ["Nouvelle valeur"]

    def test_update_from_serialized_data_skip_missing_updated_displayed_value(
        self, suggestion_groupe_with_acteur
    ):
        """Test that fields without updated_displayed_value are skipped"""
        fields_values = {
            "nom": {
                "displayed_value": "Ancien nom",
                # Pas de updated_displayed_value
                "new_value": "Nouveau nom",
                "old_value": "Ancien nom",
            }
        }
        fields_groups = [("nom",)]

        initial_count = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).count()

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Verify that no new SuggestionUnitaire has been created
        final_count = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur"
        ).count()
        assert final_count == initial_count

    def test_update_from_serialized_data_grouped_fields_partial_update(
        self, suggestion_groupe_with_acteur
    ):
        """Test update with grouped fields where only one field is updated"""
        fields_values = {
            "latitude": {
                "displayed_value": "48.1234",
                "updated_displayed_value": "48.9999",
                "new_value": "48.56789",
                "old_value": "48.1234",
            },
            "longitude": {
                "displayed_value": "2.1234",
                "updated_displayed_value": "2.1234",  # Pas de changement
                "new_value": "2.56789",
                "old_value": "2.1234",
            },
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_with_acteur, fields_values, fields_groups
        )

        assert success is True
        assert errors is None

        # Verify that the SuggestionUnitaire for (latitude, longitude) has been created
        # with latitude updated and longitude not updated
        suggestion_unitaire = suggestion_groupe_with_acteur.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
        ).first()
        assert suggestion_unitaire is not None
        # longitude is added to values_to_update during validation with displayed_value
        assert suggestion_unitaire.valeurs == ["48.9999", "2.1234"]

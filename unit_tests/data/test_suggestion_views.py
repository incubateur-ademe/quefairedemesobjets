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


@pytest.fixture
def suggestion_groupe():
    suggestion_groupe = SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            type_action=SuggestionAction.SOURCE_AJOUT,
        ),
        acteur_id="ID_UNIQUE_123",
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
def suggestion_groupe_ajout(suggestion_groupe):
    SuggestionUnitaireFactory(
        suggestion_groupe=suggestion_groupe,
        suggestion_modele="Acteur",
        champs=["identifiant_unique"],
        valeurs=["ID_UNIQUE_123"],
    )
    return suggestion_groupe


@pytest.fixture
def suggestion_groupe_modification(suggestion_groupe):
    suggestion_groupe.suggestion_cohorte.type_action = (
        SuggestionAction.SOURCE_MODIFICATION
    )
    suggestion_groupe.suggestion_cohorte.save()
    suggestion_groupe.acteur = ActeurFactory(
        identifiant_unique="ID_UNIQUE_123",
        nom="Ancien nom",
        location=Point(2.1234, 48.1234),
    )
    suggestion_groupe.identifiant_unique = suggestion_groupe.acteur.identifiant_unique

    suggestion_groupe.save()
    return suggestion_groupe


@pytest.mark.django_db
class TestSerializeSuggestionGroupe:

    def test_serialize_source_ajout_returns_expected_keys_and_values(
        self, suggestion_groupe_ajout
    ):
        """Test that SOURCE_AJOUT returns the expected keys in result"""

        expected_fields_values = {
            "identifiant_unique": {
                "acteur_suggestion_value": "ID_UNIQUE_123",
                "acteur": '<span class="suggestion-text-added">ID_UNIQUE_123</span>',
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "nom": {
                "acteur_suggestion_value": "Nouveau nom",
                "acteur": '<span class="suggestion-text-added">Nouveau nom</span>',
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "latitude": {
                "acteur_suggestion_value": "48.56789",
                "acteur": '<span class="suggestion-text-added">48.56789</span>',
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "longitude": {
                "acteur_suggestion_value": "2.56789",
                "acteur": '<span class="suggestion-text-added">2.56789</span>',
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
        }

        result = serialize_suggestion_groupe(suggestion_groupe_ajout)

        # Check keys and values
        assert result["suggestion_groupe"] == suggestion_groupe_ajout
        assert result["identifiant_unique"] == "ID_UNIQUE_123"
        assert result["fields_groups"] == [
            ("identifiant_unique",),
            ("nom",),
            ("latitude", "longitude"),
        ]
        assert result["fields_values"] == expected_fields_values

    def test_serialize_source_ajout_with_revisionacteur_suggestions(
        self, suggestion_groupe_ajout
    ):
        """Test that SOURCE_AJOUT with suggestion_unitaires of type RevisionActeur"""
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_ajout,
            suggestion_modele="RevisionActeur",
            revision_acteur_id="ID_UNIQUE_123",
            champs=["nom"],
            valeurs=["Revision nom"],
        )
        expected_fields_values_nom = {
            "acteur_suggestion_value": "Nouveau nom",
            "acteur": '<span class="suggestion-text-added">Nouveau nom</span>',
            "revision_acteur": (
                '<span class="suggestion-text-added">Revision nom</span>'
            ),
        }
        result = serialize_suggestion_groupe(suggestion_groupe_ajout)

        assert result["suggestion_groupe"] == suggestion_groupe_ajout
        assert result["identifiant_unique"] == "ID_UNIQUE_123"
        assert ("nom",) in result["fields_groups"]
        assert result["fields_values"]["nom"] == expected_fields_values_nom

    def test_serialize_source_modification_returns_expected_keys_and_values(
        self,
        suggestion_groupe_modification,
    ):
        """Test SOURCE_MODIFICATION with an acteur but no revision_acteur"""

        expected_fields_values = {
            "nom": {
                "acteur_suggestion_value": "Nouveau nom",
                "acteur": (
                    '<span class="suggestion-text-removed">Ancien'
                    '</span><span class="suggestion-text-added">Nouveau</span> nom'
                ),
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "latitude": {
                "acteur_suggestion_value": "48.56789",
                "acteur": (
                    '48.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "longitude": {
                "acteur_suggestion_value": "2.56789",
                "acteur": (
                    '2.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">-</span>',
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
        }

        result = serialize_suggestion_groupe(suggestion_groupe_modification)

        # Check keys and values
        assert result["acteur"] == suggestion_groupe_modification.acteur
        assert result["revision_acteur"] is None
        assert result["parent_revision_acteur"] is None
        assert result["fields_values"] == expected_fields_values

    def test_serialize_source_modification_with_revisionacteur(
        self,
        suggestion_groupe_modification,
    ):
        """Test SOURCE_MODIFICATION with a revision_acteur"""
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.save()

        expected_fields_values = {
            "nom": {
                "acteur_suggestion_value": "Nouveau nom",
                "acteur": (
                    '<span class="suggestion-text-removed">Ancien'
                    '</span><span class="suggestion-text-added">Nouveau</span> nom'
                ),
                "revision_acteur": (
                    '<span class="no-suggestion-text">Revision nom</span>'
                ),
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "latitude": {
                "acteur_suggestion_value": "48.56789",
                "acteur": (
                    '48.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">48.01</span>',
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
            "longitude": {
                "acteur_suggestion_value": "2.56789",
                "acteur": (
                    '2.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">2.01</span>',
                "parent_revision_acteur": '<span class="no-suggestion-text">-</span>',
            },
        }

        result = serialize_suggestion_groupe(suggestion_groupe_modification)

        assert result["acteur"] == suggestion_groupe_modification.acteur
        assert result["revision_acteur"] == revision_acteur
        assert result["parent_revision_acteur"] is None

        assert result["fields_values"] == expected_fields_values

    def test_serialize_source_modification_with_revisionacteur_and_parent(
        self,
        suggestion_groupe_modification,
    ):
        """Test SOURCE_MODIFICATION with a parent revision_acteur"""
        parent_revision_acteur = RevisionActeurFactory(
            nom="Parent nom",
            location=Point(2.1111, 48.1111),
        )
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=suggestion_groupe_modification.acteur.identifiant_unique,
            nom="Revision nom",
            location=Point(2.01, 48.01),
            parent=parent_revision_acteur,
        )
        suggestion_groupe_modification.revision_acteur = revision_acteur
        suggestion_groupe_modification.parent_revision_acteur = parent_revision_acteur
        suggestion_groupe_modification.save()

        expected_fields_values = {
            "nom": {
                "acteur_suggestion_value": "Nouveau nom",
                "acteur": (
                    '<span class="suggestion-text-removed">Ancien'
                    '</span><span class="suggestion-text-added">Nouveau</span> nom'
                ),
                "revision_acteur": (
                    '<span class="no-suggestion-text">Revision nom</span>'
                ),
                "parent_revision_acteur": (
                    '<span class="no-suggestion-text">Parent nom</span>'
                ),
            },
            "latitude": {
                "acteur_suggestion_value": "48.56789",
                "acteur": (
                    '48.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">48.01</span>',
                "parent_revision_acteur": (
                    '<span class="no-suggestion-text">48.1111</span>'
                ),
            },
            "longitude": {
                "acteur_suggestion_value": "2.56789",
                "acteur": (
                    '2.<span class="suggestion-text-removed">1234'
                    '</span><span class="suggestion-text-added">56789</span>'
                ),
                "revision_acteur": '<span class="no-suggestion-text">2.01</span>',
                "parent_revision_acteur": (
                    '<span class="no-suggestion-text">2.1111</span>'
                ),
            },
        }

        result = serialize_suggestion_groupe(suggestion_groupe_modification)

        # Check keys and values
        assert result["acteur"] == suggestion_groupe_modification.acteur
        assert result["revision_acteur"] == revision_acteur
        assert result["parent_revision_acteur"] == parent_revision_acteur
        assert result["fields_values"] == expected_fields_values

    def test_serialize_source_modification_with_parent_revision_acteur_suggestion(
        self,
        suggestion_groupe_modification,
    ):
        """Test SOURCE_MODIFICATION with ParentRevisionActeur suggestion unitaires"""
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
        suggestion_groupe_modification.parent_revision_acteur = revision_acteur_parent
        suggestion_groupe_modification.save()

        # Ajouter une suggestion pour ParentRevisionActeur
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="ParentRevisionActeur",
            parent_revision_acteur=revision_acteur_parent,
            champs=["nom"],
            valeurs=["Suggestion Parent nom"],
        )
        expected_fields_values_nom = {
            "acteur_suggestion_value": "Nouveau nom",
            "acteur": (
                '<span class="suggestion-text-removed">Ancien'
                '</span><span class="suggestion-text-added">Nouveau</span> nom'
            ),
            "revision_acteur": '<span class="no-suggestion-text">Revision nom</span>',
            "parent_revision_acteur": (
                '<span class="suggestion-text-added">Suggestion </span>Parent nom'
            ),
        }

        result = serialize_suggestion_groupe(suggestion_groupe_modification)

        print(result["fields_values"]["nom"])
        assert result["fields_values"]["nom"] == expected_fields_values_nom

    def test_serialize_source_modification_without_acteur_raises_error(self):
        """Test that SOURCE_MODIFICATION without acteur raises ValueError"""
        suggestion_groupe = SuggestionGroupeFactory(
            suggestion_cohorte=SuggestionCohorteFactory(
                type_action=SuggestionAction.SOURCE_MODIFICATION,
            ),
            acteur=None,  # Pas d'acteur
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )

        with pytest.raises(ValueError) as exc_info:
            serialize_suggestion_groupe(suggestion_groupe)

        assert "acteur is required" in str(exc_info.value)


@pytest.mark.django_db
class TestUpdateSuggestionGroupe:
    @pytest.fixture
    def test_update_suggestion_groupe_ajout_with_nom(self, suggestion_groupe_ajout):
        """Test successful update with a single field"""
        fields_values = {"nom": "Nom mis à jour"}
        fields_groups = [("nom",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_ajout,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_ajout.refresh_from_db()
        suggestion_unitaire = suggestion_groupe_ajout.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()

        assert success is True
        assert errors is None
        assert suggestion_groupe_ajout.acteur_id == "ID_UNIQUE_123"
        # FIXME : should we add a revision_acteur_id to the suggestion_groupe ?
        # assert suggestion_groupe_ajout.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["nom"]
        assert suggestion_unitaire.valeurs == ["Nom mis à jour"]

    def test_update_suggestion_groupe_ajout_with_latlong(self, suggestion_groupe_ajout):
        """Test successful update with grouped fields (latitude/longitude)"""
        fields_values = {
            "latitude": "48.9999",
            "longitude": "2.9999",
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_ajout,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_ajout.refresh_from_db()
        suggestion_unitaire = suggestion_groupe_ajout.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
        ).first()

        assert success is True
        assert errors is None
        assert suggestion_groupe_ajout.acteur_id == "ID_UNIQUE_123"
        # FIXME : should we add a revision_acteur_id to the suggestion_groupe ?
        # assert suggestion_groupe_ajout.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["latitude", "longitude"]
        assert suggestion_unitaire.valeurs == ["48.9999", "2.9999"]

    def test_update_suggestion_groupe_ajout_with_nom_and_latlong(
        self, suggestion_groupe_ajout
    ):
        """Test successful update with multiple fields"""
        fields_values = {
            "nom": "Nom mis à jour",
            "latitude": "48.9999",
            "longitude": "2.9999",
        }
        fields_groups = [("nom",), ("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_ajout,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_ajout.refresh_from_db()
        suggestion_unitaire_nom = suggestion_groupe_ajout.suggestion_unitaires.filter(
            suggestion_modele="RevisionActeur", champs=["nom"]
        ).first()
        suggestion_unitaire_latlong = (
            suggestion_groupe_ajout.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
            ).first()
        )

        assert success is True
        assert errors is None

        # Verify that the two SuggestionUnitaires have been created
        assert suggestion_unitaire_nom is not None
        assert suggestion_unitaire_nom.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire_nom.acteur_id is None
        assert suggestion_unitaire_nom.champs == ["nom"]
        assert suggestion_unitaire_nom.valeurs == ["Nom mis à jour"]
        assert suggestion_unitaire_latlong is not None
        assert suggestion_unitaire_latlong.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire_latlong.acteur_id is None
        assert suggestion_unitaire_latlong.champs == ["latitude", "longitude"]
        assert suggestion_unitaire_latlong.valeurs == ["48.9999", "2.9999"]

    def test_update_error_invalid_longitude(self, suggestion_groupe_ajout):
        """Test error when longitude is not a valid float"""
        fields_values = {
            "longitude": "not_a_float",
            "latitude": "48.9999",
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_ajout,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )

        assert success is False
        assert errors is not None
        # The error should be related to latitude or longitude
        assert any(
            "latitude" in str(errors).lower() or "longitude" in str(errors).lower()
            for key in errors
        )

    def test_update_suggestion_groupe_modification_with_nom(
        self, suggestion_groupe_modification
    ):
        """
        Test update when a RevisionActeur suggestion does not exist
        """

        fields_values = {"nom": "Nouvelle valeur"}
        fields_groups = [("nom",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_modification.refresh_from_db()
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["nom"]
            ).first()
        )

        assert success is True
        assert errors is None
        # Verify that the SuggestionUnitaire has been created
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["nom"]
        assert suggestion_unitaire.valeurs == ["Nouvelle valeur"]

    def test_update_suggestion_groupe_modification_with_nom_on_existing_sugg(
        self, suggestion_groupe_modification
    ):
        """
        Test update when a RevisionActeur suggestion already exists with different value
        """
        # Create a RevisionActeur suggestion
        suggestion_unitaire_nom_existing = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="RevisionActeur",
            revision_acteur_id="ID_UNIQUE_123",
            champs=["nom"],
            valeurs=["Ancienne valeur"],
        )

        fields_values = {"nom": "Nouvelle valeur"}
        fields_groups = [("nom",)]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_modification.refresh_from_db()
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["nom"]
            ).first()
        )

        assert success is True
        assert errors is None
        # Verify that the SuggestionUnitaire has been updated
        assert suggestion_unitaire is not None
        assert suggestion_unitaire_nom_existing.id == suggestion_unitaire.id
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["nom"]
        assert suggestion_unitaire.valeurs == ["Nouvelle valeur"]

    def test_update_suggestion_groupe_modification_with_latlong(
        self, suggestion_groupe_modification
    ):
        """
        Test update when a RevisionActeur suggestion does not exist
        """

        fields_values = {"latitude": "48.8566", "longitude": "2.3522"}
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_modification.refresh_from_db()
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
            ).first()
        )

        assert success is True
        assert errors is None
        # Verify that the SuggestionUnitaire has been created
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["latitude", "longitude"]
        assert suggestion_unitaire.valeurs == ["48.8566", "2.3522"]

    def test_update_suggestion_groupe_modification_with_latlong_on_existing_sugg(
        self, suggestion_groupe_modification
    ):
        """
        Test update when a RevisionActeur suggestion already exists with different value
        """
        # Create a RevisionActeur suggestion
        suggestion_unitaire_latlong_existing = SuggestionUnitaireFactory(
            suggestion_groupe=suggestion_groupe_modification,
            suggestion_modele="RevisionActeur",
            revision_acteur_id="ID_UNIQUE_123",
            champs=["latitude", "longitude"],
            valeurs=["45.7640", "4.8357"],
        )

        fields_values = {"latitude": "48.8566", "longitude": "2.3522"}
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )
        suggestion_groupe_modification.refresh_from_db()
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
            ).first()
        )

        assert success is True
        assert errors is None
        # Verify that the SuggestionUnitaire has been updated
        assert suggestion_unitaire is not None
        assert suggestion_unitaire_latlong_existing.id == suggestion_unitaire.id
        assert suggestion_unitaire.revision_acteur_id == "ID_UNIQUE_123"
        assert suggestion_unitaire.acteur_id is None
        assert suggestion_unitaire.champs == ["latitude", "longitude"]
        assert suggestion_unitaire.valeurs == ["48.8566", "2.3522"]

    def test_update_suggestion_groupe_modification_on_parent(
        self, suggestion_groupe_modification
    ):
        """Test update with ParentRevisionActeur suggestion_modele"""
        fields_values = {"nom": "Parent nom mis à jour"}
        fields_groups = [("nom",)]
        parent_revision_acteur = RevisionActeurFactory(
            identifiant_unique="ID_PARENT_456",
            nom="Parent nom",
            location=Point(2.1234, 48.1234),
        )
        suggestion_groupe_modification.parent_revision_acteur = parent_revision_acteur
        suggestion_groupe_modification.save()

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "ParentRevisionActeur",
            fields_values,
            fields_groups,
        )

        assert success is True
        assert errors is None

        # Vérifier que le SuggestionUnitaire a été créé avec le bon modèle
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="ParentRevisionActeur", champs=["nom"]
            ).first()
        )
        assert suggestion_unitaire.parent_revision_acteur_id == "ID_PARENT_456"
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.valeurs == ["Parent nom mis à jour"]

    def test_update_grouped_fields_partial_update(self, suggestion_groupe_modification):
        """Test update with grouped fields where only one field is updated"""
        fields_values = {
            "latitude": "48.9999",
            "longitude": "2.1234",  # Pas de changement
        }
        fields_groups = [("latitude", "longitude")]

        success, errors = update_suggestion_groupe(
            suggestion_groupe_modification,
            "RevisionActeur",
            fields_values,
            fields_groups,
        )

        assert success is True
        assert errors is None

        # Verify that the SuggestionUnitaire for (latitude, longitude) has been created
        suggestion_unitaire = (
            suggestion_groupe_modification.suggestion_unitaires.filter(
                suggestion_modele="RevisionActeur", champs=["latitude", "longitude"]
            ).first()
        )
        assert suggestion_unitaire is not None
        assert suggestion_unitaire.valeurs == ["48.9999", "2.1234"]

    def test_update_invalid_suggestion_modele(self, suggestion_groupe_modification):
        """Test that invalid suggestion_modele raises ValueError"""
        fields_values = {"nom": "Test"}
        fields_groups = [("nom",)]

        with pytest.raises(ValueError) as exc_info:
            update_suggestion_groupe(
                suggestion_groupe_modification,
                "InvalidModele",
                fields_values,
                fields_groups,
            )

        assert "Invalid suggestion_modele" in str(exc_info.value)

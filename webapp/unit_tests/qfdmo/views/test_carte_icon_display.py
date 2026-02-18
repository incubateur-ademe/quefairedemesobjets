"""
Test for icon display issue in carte view.

This test reproduces the bug where icons from non-selected groupe_actions
appear on the carte despite not being selected by the user.
"""

import pytest
from django.test import Client
from django.urls import reverse
from factory.django import FileField

from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory
from unit_tests.qfdmo.carte_config_factory import (
    CarteConfigFactory,
    GroupeActionConfigFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.mark.django_db
class TestCarteIconDisplay:
    """Test that only icons from selected groupe_actions are displayed"""

    @pytest.fixture
    def sous_categorie_109(self):
        """Create or get sous_categorie with ID 109"""
        return SousCategorieObjetFactory(id=109, libelle="Test objet mauvais état")

    @pytest.fixture
    def groupe_reparer(self):
        """Get 'reparer' groupe_action from fixtures"""
        from qfdmo.models import GroupeAction

        # Use the existing groupe_action from fixtures
        return GroupeAction.objects.get(code="reparer")

    @pytest.fixture
    def groupe_donner(self):
        """Create 'donner_test' groupe_action - should not appear in results"""
        groupe = GroupeActionFactory(code="donner_test")
        return groupe

    @pytest.fixture
    def groupe_trier(self):
        """Get 'trier' groupe_action from fixtures"""
        from qfdmo.models import GroupeAction

        # Use the existing groupe_action from fixtures
        return GroupeAction.objects.get(code="trier")

    @pytest.fixture
    def action_reparer(self, groupe_reparer):
        """Get 'reparer' action from fixtures"""
        # The action is already linked to groupe_reparer from fixtures
        return groupe_reparer.actions.first()

    @pytest.fixture
    def action_donner(self, groupe_donner):
        """Create 'donner_test' action"""
        action = ActionFactory(
            code="donner_test",
            icon="fr-icon-gift-fill",
            couleur="#ff5733",
        )
        groupe_donner.actions.add(action)
        return action

    @pytest.fixture
    def action_trier(self, groupe_trier):
        """Get 'trier' action from fixtures"""
        # The action is already linked to groupe_trier from fixtures
        return groupe_trier.actions.first()

    @pytest.fixture
    def carte_config_mauvais_etat(self, groupe_reparer, groupe_trier, groupe_donner):
        """Create carte config matching 'mauvais-etat' configuration"""
        carte = CarteConfigFactory(
            slug="mauvais-etat",
            nom="Objets en mauvais état",
        )
        # Only reparer and trier are configured, NOT donner
        carte.groupe_action.add(groupe_reparer)
        carte.groupe_action.add(groupe_trier)

        # Add groupe_action_configs with custom icons
        # Set acteur_type=None so the icons apply to all acteur types
        GroupeActionConfigFactory(
            carte_config=carte,
            groupe_action=groupe_reparer,
            icon=FileField(filename="icon-reparer.svg"),
            acteur_type=None,
        )
        GroupeActionConfigFactory(
            carte_config=carte,
            groupe_action=groupe_trier,
            icon=FileField(filename="icon-trier.svg"),
            acteur_type=None,
        )
        # Note: No config for groupe_donner

        return carte

    @pytest.fixture
    def acteur_with_multiple_actions(
        self, sous_categorie_109, action_reparer, action_donner, action_trier
    ):
        """Create an acteur that has reparer, donner AND trier actions"""
        from django.contrib.gis.geos import Point

        # Create acteur near Auray coordinates for the search
        acteur = DisplayedActeurFactory(
            nom="Test Acteur with Multiple Actions",
            location=Point(-2.990838, 47.668099, srid=4326),
            statut="ACTIF",
        )

        # Add proposition services for all three actions
        ps_reparer = DisplayedPropositionServiceFactory(
            acteur=acteur, action=action_reparer
        )
        ps_reparer.sous_categories.add(sous_categorie_109)

        ps_donner = DisplayedPropositionServiceFactory(
            acteur=acteur, action=action_donner
        )
        ps_donner.sous_categories.add(sous_categorie_109)

        ps_trier = DisplayedPropositionServiceFactory(
            acteur=acteur, action=action_trier
        )
        ps_trier.sous_categories.add(sous_categorie_109)

        return acteur

    def test_icon_lookup_only_contains_selected_groupe_actions(
        self,
        carte_config_mauvais_etat,
        acteur_with_multiple_actions,
        sous_categorie_109,
        groupe_reparer,
        groupe_trier,
        groupe_donner,
    ):
        """
        Test the specific URL from the issue:
        /carte/mauvais-etat/?querystring=c291c19jYXRlZ29yaWVfb2JqZXQ9MTA5&adresse=Auray&...

        This should NOT display the 'donner' icon since only 'reparer' and 'trier'
        are selected in the carte config.
        """
        client = Client()

        # Build the URL with all parameters from the issue
        url = reverse("qfdmo:carte_custom", kwargs={"slug": "mauvais-etat"})
        params = {
            "map_container_id": "mauvais-etat",
            # sous_categorie_objet=109
            "querystring": "c291c19jYXRlZ29yaWVfb2JqZXQ9MTA5",
            "adresse": "Auray",
            "longitude": "-2.990838",
            "latitude": "47.668099",
            "view_mode-view": "carte",
            "carte": "",
            "r": "506",
            "bounding_box": "",
            "filtres-pas_exclusivite_reparation": "on",
        }

        response = client.get(url, params)

        assert response.status_code == 200

        # Check that the context contains icon_lookup
        icon_lookup = response.context.get("icon_lookup", {})

        # Verify icon_lookup only contains entries for reparer and trier actions
        # NOT for donner
        action_codes_in_lookup = {key[0] for key in icon_lookup.keys() if key[0]}

        assert "reparer" in action_codes_in_lookup, "reparer should be in icon_lookup"
        assert "trier" in action_codes_in_lookup, "trier should be in icon_lookup"
        assert (
            "donner_test" not in action_codes_in_lookup
        ), "donner_test should NOT be in icon_lookup since it's not selected"

        # Additional check: verify the selected_action_codes in context
        selected_action_codes = response.context.get("selected_action_codes", "")
        action_codes = selected_action_codes.split("|") if selected_action_codes else []

        assert "reparer" in action_codes, "reparer should be in selected_action_codes"
        assert "trier" in action_codes, "trier should be in selected_action_codes"
        assert (
            "donner_test" not in action_codes
        ), "donner_test should NOT be in selected_action_codes"

    def test_icon_lookup_with_explicit_legende_selection(
        self,
        carte_config_mauvais_etat,
        acteur_with_multiple_actions,
        sous_categorie_109,
        groupe_reparer,
        groupe_trier,
        groupe_donner,
    ):
        """
        Test that when only reparer is selected in the legende form,
        only reparer icons appear in icon_lookup.
        """
        client = Client()

        url = reverse("qfdmo:carte_custom", kwargs={"slug": "mauvais-etat"})
        params = {
            "map_container_id": "mauvais-etat",
            "querystring": "c291c19jYXRlZ29yaWVfb2JqZXQ9MTA5",
            "adresse": "Auray",
            "longitude": "-2.990838",
            "latitude": "47.668099",
            "view_mode-view": "carte",
            # Explicitly select only reparer in the legend
            # Note: groupe_action is a MultipleChoiceField, so we need to pass a list
            "mauvais-etat_legende-groupe_action": [str(groupe_reparer.id)],
        }

        response = client.get(url, params)

        assert response.status_code == 200

        icon_lookup = response.context.get("icon_lookup", {})
        action_codes_in_lookup = {key[0] for key in icon_lookup.keys() if key[0]}

        # Only reparer should be in the lookup
        assert "reparer" in action_codes_in_lookup, "reparer should be in icon_lookup"
        assert (
            "trier" not in action_codes_in_lookup
        ), "trier should NOT be in icon_lookup (not selected)"
        assert (
            "donner_test" not in action_codes_in_lookup
        ), "donner_test should NOT be in icon_lookup (not in carte config)"

    def test_acteur_displayed_with_correct_icon(
        self,
        carte_config_mauvais_etat,
        acteur_with_multiple_actions,
        sous_categorie_109,
        groupe_reparer,
        groupe_trier,
    ):
        """
        Test that acteurs in the response only show icons from selected groupe_actions.
        """
        client = Client()

        url = reverse("qfdmo:carte_custom", kwargs={"slug": "mauvais-etat"})
        params = {
            "map_container_id": "mauvais-etat",
            "querystring": "c291c19jYXRlZ29yaWVfb2JqZXQ9MTA5",
            "mauvais-etat_map-adresse": "Auray",
            "mauvais-etat_map-longitude": "-2.990838",
            "mauvais-etat_map-latitude": "47.668099",
            "view_mode-view": "carte",
            "mauvais-etat_legende-groupe_action": [
                str(groupe_reparer.id),
                str(groupe_trier.id),
            ],
        }

        response = client.get(url, params)

        assert response.status_code == 200

        # Check that acteurs are in the context
        acteurs = response.context.get("acteurs", [])

        # Verify our test acteur is included
        acteur_pks = [acteur.pk for acteur in acteurs]
        assert (
            acteur_with_multiple_actions.pk in acteur_pks
        ), "Test acteur should be in results"

        # Verify the icon_lookup doesn't contain donner_test
        icon_lookup = response.context.get("icon_lookup", {})
        action_codes_in_lookup = {key[0] for key in icon_lookup.keys() if key[0]}

        assert (
            "donner_test" not in action_codes_in_lookup
        ), "donner_test icon should never appear in icon_lookup"

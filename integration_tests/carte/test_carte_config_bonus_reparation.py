import pytest
from django.contrib.gis.geos import Point, Polygon
from django.core.management import call_command

from qfdmo.models import CarteConfig, LabelQualite
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Load fixtures needed for the test"""
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "actions",
            "labels",
            "acteur_services",
            "acteur_types",
        )


@pytest.mark.django_db
class TestCarteConfigBonusReparation:
    """Test that CarteConfig filters acteurs by bonus réparation correctly"""

    def test_carte_config_with_bonus_reparation_only_shows_bonus_acteurs(self, client):
        """
        Create a CarteConfig with bonus_reparation=True and a bounding box
        covering France. Create acteurs with locations in France - one with
        a bonus label, others without.
        Check that only the acteur with the bonus label appears in the context.
        """
        # Get a bonus réparation label
        bonus_label = LabelQualite.objects.filter(bonus=True).first()
        assert bonus_label is not None, "Need at least one bonus label in fixtures"

        # Create a CarteConfig with bonus_reparation enabled and France bounding box
        # Bounding box covering all of France (approximate coordinates)
        france_bbox = Polygon.from_bbox(
            (-5.0, 41.0, 10.0, 51.0)  # (min_lng, min_lat, max_lng, max_lat)
        )

        carte_config = CarteConfig.objects.create(
            slug="test-bonus-only",
            nom="Test Bonus Réparation Only",
            bonus_reparation=True,
            bounding_box=france_bbox,
        )

        # Create test data
        action = ActionFactory()
        sous_categorie = SousCategorieObjetFactory()

        # Acteur WITH bonus label - in Paris
        acteur_with_bonus = DisplayedActeurFactory(
            nom="Réparateur Bonus Paris",
            location=Point(2.347, 48.859, srid=4326),  # Paris
            statut="ACTIF",
        )
        acteur_with_bonus.labels.add(bonus_label)
        ps1 = DisplayedPropositionServiceFactory(
            action=action, acteur=acteur_with_bonus
        )
        ps1.sous_categories.add(sous_categorie)

        # Acteur WITHOUT bonus label - in Lyon
        acteur_without_bonus_1 = DisplayedActeurFactory(
            nom="Réparateur Sans Bonus Lyon",
            location=Point(4.835, 45.764, srid=4326),  # Lyon
            statut="ACTIF",
        )
        ps2 = DisplayedPropositionServiceFactory(
            action=action, acteur=acteur_without_bonus_1
        )
        ps2.sous_categories.add(sous_categorie)

        # Another acteur WITHOUT bonus label - in Marseille
        acteur_without_bonus_2 = DisplayedActeurFactory(
            nom="Réparateur Sans Bonus Marseille",
            location=Point(5.369, 43.296, srid=4326),  # Marseille
            statut="ACTIF",
        )
        ps3 = DisplayedPropositionServiceFactory(
            action=action, acteur=acteur_without_bonus_2
        )
        ps3.sous_categories.add(sous_categorie)

        # Make a request to the CarteConfig view with search parameters
        # Use Paris as center with a large radius to cover all of France
        response = client.get(
            f"/carte/{carte_config.slug}/",
        )

        assert response.status_code == 200

        # Get the acteurs from the context
        acteurs = list(response.context.get("acteurs", []))

        # Should have exactly 1 acteur (only the one with bonus label)
        assert (
            len(acteurs) == 1
        ), f"Expected 1 acteur with bonus label, got {len(acteurs)}"

        # Verify it's the correct acteur
        assert (
            acteurs[0].pk == acteur_with_bonus.pk
        ), "The acteur should be the one with the bonus label"
        assert acteurs[0].nom == "Réparateur Bonus Paris"

        # Verify the acteur has the bonus label
        assert bonus_label in acteurs[0].labels.all()

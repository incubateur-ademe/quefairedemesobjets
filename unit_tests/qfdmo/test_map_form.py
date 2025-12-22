import json

import pytest
from django.contrib.gis.geos import Polygon

from qfdmo.forms import MapForm
from qfdmo.models import CarteConfig


@pytest.mark.django_db
class TestMapFormBoundingBoxConversion:
    """Test the bounding box conversion from CarteConfig PolygonField to JSON format"""

    def test_bounding_box_conversion_from_carte_config(self):
        """Test that bounding_box from CarteConfig is correctly
        converted to JSON format"""
        # Create a CarteConfig with a bounding box (Angers coordinates)
        bounding_box_polygon = Polygon.from_bbox(
            (
                -0.609453,
                47.457526,
                -0.51571,
                47.489048,
            )  # (min_lng, min_lat, max_lng, max_lat)
        )

        carte_config = CarteConfig.objects.create(
            slug="test-bbox-conversion",
            nom="Test Bounding Box Conversion",
            bounding_box=bounding_box_polygon,
        )

        # Create the form with the CarteConfig
        form = MapForm(carte_config=carte_config)

        # Get the initial value for bounding_box field
        bounding_box_initial = form.fields["bounding_box"].initial

        # Should be a JSON string
        assert bounding_box_initial is not None
        assert isinstance(bounding_box_initial, str)

        # Parse the JSON
        bounding_box_data = json.loads(bounding_box_initial)

        # Check the structure
        assert "southWest" in bounding_box_data
        assert "northEast" in bounding_box_data
        assert "lat" in bounding_box_data["southWest"]
        assert "lng" in bounding_box_data["southWest"]
        assert "lat" in bounding_box_data["northEast"]
        assert "lng" in bounding_box_data["northEast"]

        # Check the values (extent returns: (min_lng, min_lat, max_lng, max_lat))
        extent = bounding_box_polygon.extent
        assert bounding_box_data["southWest"]["lng"] == extent[0]
        assert bounding_box_data["southWest"]["lat"] == extent[1]
        assert bounding_box_data["northEast"]["lng"] == extent[2]
        assert bounding_box_data["northEast"]["lat"] == extent[3]

        # Check the actual values for Angers
        assert bounding_box_data["southWest"]["lng"] == -0.609453
        assert bounding_box_data["southWest"]["lat"] == 47.457526
        assert bounding_box_data["northEast"]["lng"] == -0.51571
        assert bounding_box_data["northEast"]["lat"] == 47.489048

    def test_bounding_box_conversion_with_no_carte_config(self):
        """Test that form works correctly when no CarteConfig is provided"""
        form = MapForm()

        # bounding_box field should exist but have no initial value
        assert "bounding_box" in form.fields
        assert form.fields["bounding_box"].initial is None

    def test_bounding_box_conversion_with_carte_config_but_no_bounding_box(self):
        """Test that form works when CarteConfig exists but has no bounding_box"""
        carte_config = CarteConfig.objects.create(
            slug="test-no-bbox",
            nom="Test No Bounding Box",
            bounding_box=None,
        )

        form = MapForm(carte_config=carte_config)

        # bounding_box field should exist but have no initial value
        assert "bounding_box" in form.fields
        assert form.fields["bounding_box"].initial is None

    def test_bounding_box_json_is_valid_format_for_frontend(self):
        """Test that the JSON format matches what the frontend expects"""
        bounding_box_polygon = Polygon.from_bbox((2.0, 48.0, 3.0, 49.0))

        carte_config = CarteConfig.objects.create(
            slug="test-frontend-format",
            nom="Test Frontend Format",
            bounding_box=bounding_box_polygon,
        )

        form = MapForm(carte_config=carte_config)
        bounding_box_initial = form.fields["bounding_box"].initial

        # Should be valid JSON
        bounding_box_data = json.loads(bounding_box_initial)

        # Frontend expects this exact structure
        assert set(bounding_box_data.keys()) == {"southWest", "northEast"}
        assert set(bounding_box_data["southWest"].keys()) == {"lat", "lng"}
        assert set(bounding_box_data["northEast"].keys()) == {"lat", "lng"}

        # All values should be numbers
        assert isinstance(bounding_box_data["southWest"]["lat"], (int, float))
        assert isinstance(bounding_box_data["southWest"]["lng"], (int, float))
        assert isinstance(bounding_box_data["northEast"]["lat"], (int, float))
        assert isinstance(bounding_box_data["northEast"]["lng"], (int, float))

    def test_bounding_box_extent_coordinate_order(self):
        """Test that extent coordinates are correctly mapped
        (extent order is min_x, min_y, max_x, max_y)"""
        # Create a polygon with known coordinates
        min_lng, min_lat, max_lng, max_lat = -1.5, 47.2, -1.0, 47.5
        bounding_box_polygon = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))

        carte_config = CarteConfig.objects.create(
            slug="test-extent-order",
            nom="Test Extent Order",
            bounding_box=bounding_box_polygon,
        )

        form = MapForm(carte_config=carte_config)
        bounding_box_data = json.loads(form.fields["bounding_box"].initial)

        # Verify the mapping is correct:
        # extent[0] = min_lng -> southWest.lng
        # extent[1] = min_lat -> southWest.lat
        # extent[2] = max_lng -> northEast.lng
        # extent[3] = max_lat -> northEast.lat
        assert bounding_box_data["southWest"]["lng"] == min_lng
        assert bounding_box_data["southWest"]["lat"] == min_lat
        assert bounding_box_data["northEast"]["lng"] == max_lng
        assert bounding_box_data["northEast"]["lat"] == max_lat

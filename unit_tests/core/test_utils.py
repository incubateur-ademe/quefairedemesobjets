from unittest.mock import patch

import pytest
from django.http.request import MultiValueDict, QueryDict
from django.test import RequestFactory, override_settings

from core import utils


@pytest.fixture
def request_factory():
    return RequestFactory()


@patch("core.utils.get_directions")  # replace with the actual module path
class TestGetDirection:
    def test_get_direction_for_carte(self, mock_get_directions, request_factory):
        mock_get_directions.return_value = [{"code": "north"}, {"code": "south"}]
        # Test when "carte" is in GET parameters
        request = request_factory.get("/?carte")
        assert utils.get_direction(request) is None

    @override_settings(DEFAULT_ACTION_DIRECTION="north")
    def test_get_direction_default_direction(
        self, mock_get_directions, request_factory
    ):
        mock_get_directions.return_value = [{"code": "north"}, {"code": "south"}]

        request = request_factory.get("/")
        assert utils.get_direction(request) == "north"

        request = request_factory.get("/?direction=fake")
        assert utils.get_direction(request) == "north"

    def test_get_direction_direction(self, mock_get_directions, request_factory):
        mock_get_directions.return_value = [{"code": "north"}, {"code": "south"}]

        request = request_factory.get("/?direction=north")
        assert utils.get_direction(request) == "north"

        request = request_factory.get("/?direction=south")
        assert utils.get_direction(request) == "south"


def query_dict_from(dictionary):
    query_dict = QueryDict("", mutable=True)
    query_dict.update(MultiValueDict(dictionary))
    return query_dict

import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("url", ["/api/v1/docs", "/api/docs"])
def test_each_api_has_its_documentation(client, url):
    assert client.get(url).status_code == 200

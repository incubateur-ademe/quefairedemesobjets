"""The public API v1 is mounted next to the historical one."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_api_v1_serves_its_documentation(client):
    assert client.get(reverse("api_v1:openapi-view")).status_code == 200

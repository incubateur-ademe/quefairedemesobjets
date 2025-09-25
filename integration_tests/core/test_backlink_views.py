import pytest
from factory.django import DjangoModelFactory

from qfdmd.models import EmbedSettings


class EmbedSettingsFactory(DjangoModelFactory):
    class Meta:
        model = EmbedSettings


@pytest.mark.django_db
def test_backlink_assistant(client):
    EmbedSettingsFactory(backlink_assistant="coucou")
    response = client.get("/embed/backlink?key=assistant")
    assert response.content.decode() == "coucou"


@pytest.mark.django_db
def test_backlink_carte(client):
    EmbedSettingsFactory(backlink_carte="coucou")
    response = client.get("/embed/backlink?key=carte")
    assert response.content.decode() == "coucou"


@pytest.mark.django_db
def test_backlink_formulaire(client):
    EmbedSettingsFactory(backlink_formulaire="coucou")
    response = client.get("/embed/backlink?key=formulaire")
    assert response.content.decode() == "coucou"


@pytest.mark.django_db
def test_backlink_random(client):
    EmbedSettingsFactory(
        backlink_carte="coucou", backlink_assistant="youpi", backlink_formulaire="super"
    )
    response = client.get("/embed/backlink?key=random")
    assert response.content.decode() == ""


@pytest.mark.django_db
def test_backlink_without_settings(client):
    response = client.get("/embed/backlink?key=assistant")
    assert response.content.decode() == ""

    response = client.get("/embed/backlink?key=formulaire")
    assert response.content.decode() == ""

    response = client.get("/embed/backlink?key=carte")
    assert response.content.decode() == ""

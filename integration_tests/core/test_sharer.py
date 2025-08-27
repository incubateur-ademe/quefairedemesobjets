# The dict below need to be easily copy-pasted from pytest outputs.
# Enforcing the 501 rule would make maintainig this test more difficult
# so it is bypassed here.
# flake8: noqa: E501

import pytest
from django.test import RequestFactory
from django.urls import resolve

from core.templatetags.share_tags import get_sharer_content
from unit_tests.qfdmd.qfdmod_factory import SynonymeFactory
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory


@pytest.mark.django_db()
class TestSharer:
    def test_sharer_synonyme(self):
        synonyme = SynonymeFactory(nom="Nom du synonyme", slug="coucou")
        request = RequestFactory().get(synonyme.url)
        request.resolver_match = resolve(synonyme.url)
        sharer = get_sharer_content(request, synonyme)

        assert sharer == {
            "url": "http://testserver/dechet/nom-du-synonyme/",
            "facebook": {
                "title": "partager Nom du synonyme sur Facebook - nouvelle fenêtre",
                "url": "https://www.facebook.com/sharer.php?u=http%3A%2F%2Ftestserver%2Fdechet%2Fnom-du-synonyme%2F",
            },
            "twitter": {
                "title": "partager Nom du synonyme sur X - nouvelle fenêtre",
                "url": "https://twitter.com/intent/tweet?url=http%3A%2F%2Ftestserver%2Fdechet%2Fnom-du-synonyme%2F&text=Découvrez le site de l'ADEME “Que faire de mes objets & déchets”&via=Longue+vie+aux+objets&hashtags=longuevieauxobjets,ademe",
            },
            "linkedin": {
                "title": "partager Nom du synonyme sur LinkedIn - nouvelle fenêtre",
                "url": "https://www.linkedin.com/shareArticle?url=http%3A%2F%2Ftestserver%2Fdechet%2Fnom-du-synonyme%2F&title=Découvrez le site de l'ADEME “Que faire de mes objets & déchets”",
            },
            "email": {
                "title": "partager Nom du synonyme par email - nouvelle fenêtre",
                "url": "mailto:?subject=D%C3%A9couvrez%20le%20site%20de%20l%27ADEME%20%E2%80%9CQue%20faire%20de%20mes%20objets%20%26%20d%C3%A9chets%E2%80%9D&body=Bonjour%2C%0A%20Vous%20souhaitez%20encourager%20au%20tri%20et%20la%20consommation%20responsable%2C%20le%20site%20de%20l%E2%80%99ADEME%20Que%20faire%20de%20mes%20objets%20%26%20d%C3%A9chets%20accompagne%20les%20citoyens%20gr%C3%A2ce%20%C3%A0%20des%20bonnes%20pratiques%20et%20adresses%20pr%C3%A8s%20de%20chez%20eux%2C%20pour%20%C3%A9viter%20l%27achat%20neuf%20et%20r%C3%A9duire%20les%20d%C3%A9chets.%0AD%C3%A9couvrez%20le%20ici%20%3A%20http%3A//testserver/dechet/nom-du-synonyme/",
            },
        }

    def test_sharer(self):
        displayed_acteur = DisplayedActeurFactory(nom="Coucou", uuid="un-coucou-unique")
        url = displayed_acteur.get_absolute_url()
        request = RequestFactory().get(url)
        request.resolver_match = resolve(url)
        sharer = get_sharer_content(request, displayed_acteur)

        assert sharer == {
            "url": "http://testserver/adresse_details/un-coucou-unique",
            "facebook": {
                "title": "partager Coucou sur Facebook - nouvelle fenêtre",
                "url": "https://www.facebook.com/sharer.php?u=http%3A%2F%2Ftestserver%2Fadresse_details%2Fun-coucou-unique",
            },
            "twitter": {
                "title": "partager Coucou sur X - nouvelle fenêtre",
                "url": "https://twitter.com/intent/tweet?url=http%3A%2F%2Ftestserver%2Fadresse_details%2Fun-coucou-unique&text=Découvrez le site de l'ADEME “Que faire de mes objets & déchets”&via=Longue+vie+aux+objets&hashtags=longuevieauxobjets,ademe",
            },
            "linkedin": {
                "title": "partager Coucou sur LinkedIn - nouvelle fenêtre",
                "url": "https://www.linkedin.com/shareArticle?url=http%3A%2F%2Ftestserver%2Fadresse_details%2Fun-coucou-unique&title=Découvrez le site de l'ADEME “Que faire de mes objets & déchets”",
            },
            "email": {
                "title": "partager Coucou par email - nouvelle fenêtre",
                "url": "mailto:?subject=D%C3%A9couvrez%20le%20site%20de%20l%27ADEME%20%E2%80%9CQue%20faire%20de%20mes%20objets%20%26%20d%C3%A9chets%E2%80%9D&body=Bonjour%2C%0A%20Vous%20souhaitez%20encourager%20au%20tri%20et%20la%20consommation%20responsable%2C%20le%20site%20de%20l%E2%80%99ADEME%20Que%20faire%20de%20mes%20objets%20%26%20d%C3%A9chets%20accompagne%20les%20citoyens%20gr%C3%A2ce%20%C3%A0%20des%20bonnes%20pratiques%20et%20adresses%20pr%C3%A8s%20de%20chez%20eux%2C%20pour%20%C3%A9viter%20l%27achat%20neuf%20et%20r%C3%A9duire%20les%20d%C3%A9chets.%0AD%C3%A9couvrez%20le%20ici%20%3A%20http%3A//testserver/adresse_details/un-coucou-unique",
            },
        }

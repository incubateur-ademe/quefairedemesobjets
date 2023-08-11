from django.contrib.gis.geos import Point

from qfdmo.models import NomAsNaturalKeyModel, ReemploiActeur


class TestReemploiActeurNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in ReemploiActeur.mro()


class TestReemploiActeurPoint:
    def test_longitude_Latitude(self):
        reemploi_acteur = ReemploiActeur(location=Point(1.1, 2.2))
        assert reemploi_acteur.longitude == 1.1
        assert reemploi_acteur.latitude == 2.2

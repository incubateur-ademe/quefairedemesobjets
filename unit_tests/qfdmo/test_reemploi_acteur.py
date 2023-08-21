from django.contrib.gis.geos import Point

from qfdmo.models import EconomieCirculaireActeur, NomAsNaturalKeyModel


class TestEconomieCirculaireNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in EconomieCirculaireActeur.mro()


class TestEconomieCirculairePoint:
    def test_longitude_Latitude(self):
        economie_circulaire_acteur = EconomieCirculaireActeur(location=Point(1.1, 2.2))
        assert economie_circulaire_acteur.longitude == 1.1
        assert economie_circulaire_acteur.latitude == 2.2

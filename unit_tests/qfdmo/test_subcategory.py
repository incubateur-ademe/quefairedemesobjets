from qfdmo.models import NomAsNaturalKeyModel, SousCategorieObjet


class TestSousCategorieObjetNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in SousCategorieObjet.mro()


class TestSousCategorieObjetSanitizedName:
    def test_sanitized_nom_blank(self):
        assert SousCategorieObjet(nom="").sanitized_nom == ""

    def test_sanitized_nom_specialchar(self):
        assert (
            SousCategorieObjet(nom="Établissement Français (ááíãôç@._°)").sanitized_nom
            == "ETABLISSEMENT FRANCAIS (AAIAOC@._DEG)"
        )

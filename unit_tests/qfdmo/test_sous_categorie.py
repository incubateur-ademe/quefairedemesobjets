import pytest

from qfdmo.models import CategorieObjet, NomAsNaturalKeyModel, SousCategorieObjet


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

    @pytest.mark.django_db
    def test_serialize(self):
        # Create a test instance of CategorieObjet and SousCategorieObjet
        categorie = CategorieObjet.objects.create(nom="Test Category")
        sous_categorie = SousCategorieObjet.objects.create(
            nom="Test Sous-Categorie", categorie=categorie, lvao_id=123, code="CODE"
        )

        # Call the serialize function
        serialized_sous_categorie = sous_categorie.serialize()

        # Verify that the serialized object matches what we expect
        assert serialized_sous_categorie == {
            "id": sous_categorie.id,
            "nom": "Test Sous-Categorie",
            "lvao_id": 123,
            "code": "CODE",
            "categorie": categorie.serialize(),
        }

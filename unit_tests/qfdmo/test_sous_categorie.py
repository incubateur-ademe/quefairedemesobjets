import pytest

from qfdmo.models import CategorieObjet, SousCategorieObjet


class TestActionStr:
    def test_str_blank(self):
        assert SousCategorieObjet(nom="").__str__() == ""

    def test_str_specialchar(self):
        assert SousCategorieObjet(nom="Åctïôn").__str__() == "Åctïôn"


class TestActionNaturalKey:
    def test_natural_key(self):
        assert SousCategorieObjet(nom="Natural key", code="C_00").natural_key() == (
            "C_00",
        )

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        action = SousCategorieObjet(nom="Natural key", code="C_00", categorie_id=1)
        action.save()
        assert (
            SousCategorieObjet.objects.get_by_natural_key("C_00").__str__()
            == "Natural key"
        )


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
            nom="Test Sous-Categorie", categorie=categorie, code="CODE"
        )

        # Call the serialize function
        serialized_sous_categorie = sous_categorie.serialize()

        # Verify that the serialized object matches what we expect
        assert serialized_sous_categorie == {
            "id": sous_categorie.id,
            "nom": "Test Sous-Categorie",
            "code": "CODE",
            "categorie": categorie.serialize(),
        }

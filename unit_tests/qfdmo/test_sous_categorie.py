import pytest

from qfdmo.models import CategorieObjet, SousCategorieObjet
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


class TestSousCategorieObjetStr:
    def test_str_blank(self):
        assert SousCategorieObjetFactory.build(libelle="").__str__().endswith("| ")

    def test_str_specialchar(self):
        assert (
            SousCategorieObjetFactory.build(libelle="Åctïôn")
            .__str__()
            .endswith("| Åctïôn")
        )


class TestActionNaturalKey:
    def test_natural_key(self):
        assert SousCategorieObjetFactory.build(
            libelle="Natural key", code="natural_key"
        ).natural_key() == ("natural_key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        SousCategorieObjetFactory(libelle="Natural key", code="natural_key")
        assert (
            SousCategorieObjet.objects.get_by_natural_key("natural_key")
            .__str__()
            .endswith("| Natural key")
        )


class TestSousCategorieObjetSanitizedName:
    @pytest.mark.django_db
    def test_serialize(self):
        # Create a test instance of CategorieObjet and SousCategorieObjet
        categorie = CategorieObjet.objects.create(
            libelle="Test Category", code="code_category"
        )
        sous_categorie = SousCategorieObjet.objects.create(
            libelle="Test Sous-Categorie",
            categorie=categorie,
            code="code_sous_categorie",
        )

        # Call the serialize function
        serialized_sous_categorie = sous_categorie.serialize()

        # Verify that the serialized object matches what we expect
        assert serialized_sous_categorie == {
            "afficher_carte": False,
            "qfdmd_produits": [],
            "id": sous_categorie.id,
            "libelle": "Test Sous-Categorie",
            "code": "code_sous_categorie",
            "categorie": categorie.serialize(),
            "afficher": True,
        }

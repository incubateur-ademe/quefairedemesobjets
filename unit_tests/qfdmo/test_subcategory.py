import pytest

from qfdmo.models import SubCategory


class TestSubCategoryStr:
    def test_str_blank(self):
        assert SubCategory(name="").__str__() == ""

    def test_str_specialchar(self):
        assert (
            SubCategory(name="Établissement Français (ááíãôç@._°)").__str__()
            == "Établissement Français (ááíãôç@._°)"
        )


class TestSubCategorySanitizedName:
    def test_sanitized_name_blank(self):
        assert SubCategory(name="").sanitized_name == ""

    def test_sanitized_name_specialchar(self):
        assert (
            SubCategory(name="Établissement Français (ááíãôç@._°)").sanitized_name
            == "ETABLISSEMENT FRANCAIS (AAIAOC@._DEG)"
        )


class TestCategoryNaturalKey:
    def test_natural_key(self):
        assert SubCategory(
            name="Établissement Français (ááíãôç@._°)"
        ).natural_key() == ("Établissement Français (ááíãôç@._°)",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        subcategory = SubCategory(name="Établissement Français (ááíãôç@._°)")
        subcategory.save()
        assert (
            SubCategory.objects.get_by_natural_key(
                "Établissement Français (ááíãôç@._°)"
            ).__str__()
            == "Établissement Français (ááíãôç@._°)"
        )

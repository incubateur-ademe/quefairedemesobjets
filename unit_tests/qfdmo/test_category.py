import pytest

from qfdmo.models import Category


class TestCategoryStr:
    def test_str_blank(self):
        assert Category(name="").__str__() == ""

    def test_str_specialchar(self):
        assert (
            Category(name="Établissement Français (ááíãôç@._°)").__str__()
            == "Établissement Français (ááíãôç@._°)"
        )


class TestCategoryNaturalKey:
    def test_natural_key(self):
        assert Category(name="Établissement Français (ááíãôç@._°)").natural_key() == (
            "Établissement Français (ááíãôç@._°)",
        )

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        category = Category(name="Établissement Français (ááíãôç@._°)")
        category.save()
        assert (
            Category.objects.get_by_natural_key(
                "Établissement Français (ááíãôç@._°)"
            ).__str__()
            == "Établissement Français (ááíãôç@._°)"
        )

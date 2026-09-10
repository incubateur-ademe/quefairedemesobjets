import pytest

from qfdmd.models import ConversionImmediatePage
from qfdmd.templatetags.qfdmd_tags import converts_immediately
from unit_tests.qfdmd.qfdmod_factory import PageFactory


@pytest.mark.django_db
class TestConversionImmediatePage:
    def test_page_not_listed_does_not_convert_immediately(self):
        page = PageFactory()

        assert ConversionImmediatePage.converts_immediately(page) is False

    def test_page_listed_converts_immediately(self):
        page = PageFactory()
        ConversionImmediatePage.objects.create(page=page)

        assert ConversionImmediatePage.converts_immediately(page) is True

    def test_template_filter_matches_model_method(self):
        listed = PageFactory()
        ConversionImmediatePage.objects.create(page=listed)
        unlisted = PageFactory()

        assert converts_immediately(listed) is True
        assert converts_immediately(unlisted) is False
        assert converts_immediately(None) is False

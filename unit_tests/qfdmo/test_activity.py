import pytest

from qfdmo.models import Activity


class TestActivityStr:
    def test_str_blank(self):
        assert Activity(name="").__str__() == ""

    def test_str_specialchar(self):
        assert Activity(name="Åctïôn").__str__() == "Åctïôn"


class TestActivityNaturalKey:
    def test_natural_key(self):
        assert Activity(name="Natural key").natural_key() == ("Natural key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        activity = Activity(name="Natural key")
        activity.save()
        assert (
            Activity.objects.get_by_natural_key("Natural key").__str__()
            == "Natural key"
        )

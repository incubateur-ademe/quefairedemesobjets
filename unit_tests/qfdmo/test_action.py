import pytest

from qfdmo.models import Action


class TestActionStr:
    def test_str_blank(self):
        assert Action(name="").__str__() == ""

    def test_str_specialchar(self):
        assert Action(name="Åctïôn").__str__() == "Åctïôn"


class TestActionNaturalKey:
    def test_natural_key(self):
        assert Action(name="Natural key").natural_key() == ("Natural key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        action = Action(name="Natural key")
        action.save()
        assert (
            Action.objects.get_by_natural_key("Natural key").__str__() == "Natural key"
        )

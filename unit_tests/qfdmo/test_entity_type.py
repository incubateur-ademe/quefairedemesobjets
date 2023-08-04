import pytest

from qfdmo.models import EntityType


class TestEntityTypeStr:
    def test_str_blank(self):
        assert EntityType(name="").__str__() == ""

    def test_str_specialchar(self):
        assert EntityType(name="Åctïôn").__str__() == "Åctïôn"


class TestEntityTypeNaturalKey:
    def test_natural_key(self):
        assert EntityType(name="Natural key").natural_key() == ("Natural key",)

    @pytest.mark.django_db()
    def test_get_natural_key(self):
        entity_type = EntityType(name="Natural key")
        entity_type.save()
        assert (
            EntityType.objects.get_by_natural_key("Natural key").__str__()
            == "Natural key"
        )

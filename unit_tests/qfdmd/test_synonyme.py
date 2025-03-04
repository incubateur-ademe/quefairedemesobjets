import pytest

from unit_tests.qfdmd.qfdmod_factory import SynonymeFactory


class TestSynonyme:
    @pytest.mark.django_db
    def test_str(self):
        synonyme = SynonymeFactory(nom="Nom du synonyme")
        assert str(synonyme) == "Nom du synonyme"
        assert synonyme.slug == "nom-du-synonyme"

    @pytest.mark.django_db
    def test_slug_max_length(self):
        synonyme = SynonymeFactory(nom="X" * 255)
        assert synonyme.slug == "x" * 255

    @pytest.mark.django_db
    def test_slug_max_length_with_special_characters(self):
        synonyme = SynonymeFactory(nom="X" * 255 + "é")
        assert synonyme.slug == "x" * 255

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
        synonyme255 = SynonymeFactory(nom="X" * 255)
        assert synonyme255.slug == "x" * 255

        synonyme256 = SynonymeFactory(nom="Y" * 256)
        assert synonyme256.slug == "y" * 255

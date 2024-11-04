from unit_tests.qfdmd.qfdmod_factory import SynonymeFactory


class TestSynonyme:
    def test_str(self):
        lien = SynonymeFactory.build(nom="Nom du synonyme")
        assert str(lien) == "Nom du synonyme"

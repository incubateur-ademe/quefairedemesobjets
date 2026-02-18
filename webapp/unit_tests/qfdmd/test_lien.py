from unit_tests.qfdmd.qfdmod_factory import LienFactory


class TestLien:
    def test_str(self):
        lien = LienFactory.build(titre_du_lien="lien Eco-Organisme")
        assert str(lien) == "lien Eco-Organisme"

import pytest

from unit_tests.qfdmo.acteur_factory import LabelQualiteFactory


class TestLabelQualiteStr:

    @pytest.mark.django_db
    def test_str(self):
        label = LabelQualiteFactory(
            libelle="Mon Label Qualité",
        )
        assert str(label) == "Mon Label Qualité"

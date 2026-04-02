import pytest

from core.templatetags.acteur_tags import acteur_label
from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory, LabelQualiteFactory


class TestActeurLabelTag:
    @pytest.fixture
    def acteur(self):
        return DisplayedActeurFactory()

    @pytest.fixture
    def bonus_label(self):
        return LabelQualiteFactory(code="bonus_reparation", bonus=True, afficher=True)

    @pytest.fixture
    def non_bonus_label(self):
        return LabelQualiteFactory(code="qualite_au_top", bonus=False, afficher=True)

    @pytest.mark.django_db
    def test_acteur_label_returns_empty_when_no_labels(self, acteur):
        acteur.displayable_labels_ordered = []
        result = acteur_label({}, acteur)
        assert result == {}

    @pytest.mark.django_db
    def test_acteur_label_bonus_uses_label_bonus_template(self, acteur, bonus_label):
        acteur.displayable_labels_ordered = [bonus_label]
        result = acteur_label({}, acteur)
        assert "label" in result
        # label_bonus.html injects the bonus SVG icon (not the DSFR percent icon)
        assert "icon-percent" not in result["label"]
        assert "<svg" in result["label"]

    @pytest.mark.django_db
    def test_acteur_label_bonus_sets_libelle(self, acteur, bonus_label):
        acteur.displayable_labels_ordered = [bonus_label]
        acteur_label({}, acteur)
        assert bonus_label.libelle == "Propose le Bonus Réparation"

from unittest.mock import patch

import pytest

from data.models.changes.acteur_update import ChangeActeurUpdate
from qfdmo.models.acteur import Acteur
from unit_tests.qfdmo.acteur_factory import ActeurFactory


@pytest.mark.django_db
class TestChangeActeurUpdate:
    def test_model_name(self):
        assert ChangeActeurUpdate.name() == "acteur_update"

    def test_raise_if_acteur_does_not_exist(self):
        change = ChangeActeurUpdate(id="dummy", data={"identifiant_unique": "new_id"})
        with pytest.raises(Acteur.DoesNotExist):
            change.validate()

    def test_raise_if_no_data_provided(self):
        acteur = ActeurFactory()
        change = ChangeActeurUpdate(id=acteur.pk, data={})
        with pytest.raises(ValueError, match="Aucune donnée fournie"):
            change.validate()

    @patch.object(ChangeActeurUpdate, "validate")
    def test_validate_is_called_by_apply(self, mock_validate):
        acteur = ActeurFactory(code_postal="1234")
        change = ChangeActeurUpdate(id=acteur.pk, data={"code_postal": "01234"})
        change.apply()
        mock_validate.assert_called_once()

    def test_apply_ok(self):
        # Création d'un acteur inactif avec des données de base
        acteur = ActeurFactory(
            code_postal="1234",
        )

        change = ChangeActeurUpdate(
            id=acteur.pk,
            data={"code_postal": "01234"},
        )
        change.apply()

        acteur.refresh_from_db()

        assert acteur.code_postal == "01234"

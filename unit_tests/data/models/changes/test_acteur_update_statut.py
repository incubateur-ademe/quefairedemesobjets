from unittest.mock import patch

import pytest

from data.models.changes.acteur_update_statut import ChangeActeurUpdateStatut
from qfdmo.models import RevisionActeur
from unit_tests.qfdmo.acteur_factory import ActeurFactory


@pytest.mark.django_db
class TestChangeActeurUpdateStatut:
    def test_model_name(self):
        assert ChangeActeurUpdateStatut.name() == "acteur_update_statut"

    def test_raise_if_no_data_provided(self):
        change = ChangeActeurUpdateStatut(id="dummy", data={})
        with pytest.raises(ValueError, match="No data provided"):
            change.validate()

    def test_raise_if_no_statut_provided(self):
        change = ChangeActeurUpdateStatut(id="dummy", data={"siret_is_closed": True})
        with pytest.raises(ValueError, match="No statut provided"):
            change.validate()

    def test_raise_if_invalid_statut_provided(self):
        change = ChangeActeurUpdateStatut(id="dummy", data={"statut": "not_active"})
        with pytest.raises(ValueError, match="Invalid statut"):
            change.validate()

    def test_raise_if_column_not_allowed(self):
        change = ChangeActeurUpdateStatut(
            id="dummy", data={"statut": "ACTIF", "fake": "boo"}
        )
        with pytest.raises(
            ValueError,
            match="Invalid data, only statut and siret_is_closed are allowed",
        ):
            change.validate()

    @patch.object(ChangeActeurUpdateStatut, "validate")
    def test_validate_is_called_by_apply(self, mock_validate):
        acteur = ActeurFactory()
        change = ChangeActeurUpdateStatut(id=acteur.pk, data={"statut": "INACTIF"})
        change.apply()
        mock_validate.assert_called_once()

    def test_with_acteur(self):
        acteur = ActeurFactory()
        change = ChangeActeurUpdateStatut(
            id=acteur.pk, data={"statut": "INACTIF", "siret_is_closed": True}
        )

        change.apply()
        acteur.refresh_from_db()

        assert acteur.statut == "INACTIF"
        assert acteur.siret_is_closed is True

        revision_acteur = RevisionActeur.objects.filter(pk=acteur.pk).first()
        assert revision_acteur is None

    def test_with_revision_acteur(self):
        acteur = ActeurFactory()
        revision_acteur = acteur.get_or_create_revision()
        change = ChangeActeurUpdateStatut(
            id=revision_acteur.pk, data={"statut": "INACTIF", "siret_is_closed": True}
        )

        change.apply()
        acteur.refresh_from_db()
        revision_acteur.refresh_from_db()

        assert acteur.statut == "INACTIF"
        assert acteur.siret_is_closed is True
        assert revision_acteur.statut == "INACTIF"
        assert revision_acteur.siret_is_closed is True

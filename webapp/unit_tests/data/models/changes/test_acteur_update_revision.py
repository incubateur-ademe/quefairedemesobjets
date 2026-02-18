from unittest.mock import patch

import pytest

from data.models.changes.acteur_update_revision import ChangeActeurUpdateRevision
from qfdmo.models import ActeurStatus, RevisionActeur
from unit_tests.qfdmo.acteur_factory import ActeurFactory, PropositionServiceFactory


@pytest.mark.django_db
class TestChangeActeurUpdateRsevision:
    def test_model_name(self):
        assert ChangeActeurUpdateRevision.name() == "acteur_update_revision"

    def test_raise_if_acteur_does_not_exist(self):
        change = ChangeActeurUpdateRevision(
            id="dummy", data={"identifiant_unique": "new_id"}
        )
        with pytest.raises(ValueError, match="L'acteur cible dummy n'existe pas"):
            change.validate()

    def test_raise_if_no_data_provided(self):
        acteur = ActeurFactory()
        change = ChangeActeurUpdateRevision(id=acteur.pk, data={})
        with pytest.raises(ValueError, match="Aucune donnée fournie"):
            change.validate()

    @patch.object(ChangeActeurUpdateRevision, "validate")
    def test_validate_is_called_by_apply(self, mock_validate):
        acteur = ActeurFactory(statut=ActeurStatus.INACTIF)
        change = ChangeActeurUpdateRevision(id=acteur.pk, data={"statut": "ACTIF"})
        change.apply()
        mock_validate.assert_called_once()

    def test_without_revision_ok(self):
        # Création d'un acteur inactif avec des données de base
        acteur = ActeurFactory(
            nom="foo",
            statut=ActeurStatus.ACTIF,
        )
        proposition = PropositionServiceFactory()
        acteur.proposition_services.add(proposition)

        change = ChangeActeurUpdateRevision(
            id=acteur.pk,
            data={"nom": "bar", "statut": ActeurStatus.INACTIF},
        )
        change.apply()

        assert acteur.statut == ActeurStatus.ACTIF
        assert acteur.nom == "foo"
        assert acteur.proposition_services.count() == 1

        revision = RevisionActeur.objects.get(pk=acteur.pk)

        assert revision.statut == ActeurStatus.INACTIF
        assert revision.nom == "bar"
        assert revision.proposition_services.count() == 1

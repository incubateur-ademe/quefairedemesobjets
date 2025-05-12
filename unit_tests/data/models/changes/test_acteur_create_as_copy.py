from unittest.mock import patch

import pytest

from data.models.changes.acteur_create_as_copy import ChangeActeurCreateAsCopy
from qfdmo.models import Acteur, ActeurStatus, RevisionActeur
from unit_tests.qfdmo.acteur_factory import ActeurFactory, PropositionServiceFactory


@pytest.mark.django_db
class TestChangeActeurCreateAsCopy:
    def test_model_name(self):
        assert ChangeActeurCreateAsCopy.name() == "acteur_create_as_copy"

    def test_raise_if_acteur_does_not_exist(self):
        change = ChangeActeurCreateAsCopy(
            id="dummy", data={"identifiant_unique": "new_id"}
        )
        with pytest.raises(ValueError):
            change.validate()

    def test_raise_if_no_identifiant_unique_provided(self):
        acteur = ActeurFactory()
        change = ChangeActeurCreateAsCopy(id=acteur.pk, data={})
        with pytest.raises(
            ValueError, match="l'acteur cible doit surdefinir son identifiant_unique"
        ):
            change.validate()

    def test_raise_if_same_identifiant_unique(self):
        acteur = ActeurFactory()
        change = ChangeActeurCreateAsCopy(
            id=acteur.pk, data={"identifiant_unique": acteur.identifiant_unique}
        )
        with pytest.raises(
            ValueError,
            match="l'acteur cible doit avoir un identifiant_unique différent",
        ):
            change.validate()

    @patch.object(ChangeActeurCreateAsCopy, "validate")
    def test_validate_is_called_by_apply(self, mock_validate):
        acteur = ActeurFactory(statut=ActeurStatus.INACTIF)
        change = ChangeActeurCreateAsCopy(
            id=acteur.pk, data={"identifiant_unique": "new_id"}
        )
        change.apply()
        mock_validate.assert_called_once()

    def test_raise_if_source_acteur_is_active(self):
        acteur = ActeurFactory(statut=ActeurStatus.ACTIF)
        change = ChangeActeurCreateAsCopy(
            id=acteur.pk, data={"identifiant_unique": "new_id"}
        )
        with pytest.raises(ValueError, match="ne doit pas être actif"):
            change.apply()

    def test_working_case(self):
        # Création d'un acteur inactif avec des données de base
        acteur_to_copy = ActeurFactory(
            nom="test",
            statut=ActeurStatus.INACTIF,
        )
        proposition = PropositionServiceFactory()
        acteur_to_copy.proposition_services.add(proposition)

        change = ChangeActeurCreateAsCopy(
            id=acteur_to_copy.pk,
            data={"identifiant_unique": "new_id", "statut": ActeurStatus.ACTIF},
        )
        change.apply()

        assert acteur_to_copy.statut == ActeurStatus.INACTIF

        # Revision exists
        revision_acteur_to_copy = RevisionActeur.objects.get(pk=acteur_to_copy.pk)
        assert revision_acteur_to_copy is not None
        assert revision_acteur_to_copy.proposition_services.count() == 1
        assert revision_acteur_to_copy.statut == ActeurStatus.INACTIF

        # New acteur created
        new_acteur = Acteur.objects.get(identifiant_unique="new_id")
        assert new_acteur.nom == "test"
        assert new_acteur.acteur_type == acteur_to_copy.acteur_type
        assert new_acteur.source == acteur_to_copy.source
        assert new_acteur.location == acteur_to_copy.location
        assert new_acteur.statut == ActeurStatus.ACTIF

        assert new_acteur.proposition_services.count() == 1

        new_revision_acteur = RevisionActeur.objects.get(pk=new_acteur.pk)
        assert new_revision_acteur is not None
        assert new_revision_acteur.statut == ActeurStatus.ACTIF
        assert new_revision_acteur.proposition_services.count() == 1

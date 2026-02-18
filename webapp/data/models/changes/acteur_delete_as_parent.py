"""change model to delete a parent"""

import logging

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import RevisionActeur
from qfdmo.models.acteur import ActeurStatus

logger = logging.getLogger(__name__)


class ChangeActeurDeleteAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_delete_as_parent"

    def validate(self):
        # We can't perform the verification of the deleted acteur here
        # because when we validate suggestions, necessary changes
        # haven't occured yet
        pass

    def apply(self):
        self.validate()
        """If our overall acteur management logic is working correctly,
        we should not have to delete a parent here as:
         - we should first take care of its children (e.g. pointing to new parent)
         - consequently the parent should be automatically deleted (see PR1247)
         - Except if there is some children with non actif status, then we have to
           unlink children and delete the parent
        """
        rev = RevisionActeur.objects.filter(identifiant_unique=self.id).first()
        if rev is not None:
            duplicats = rev.duplicats.all()
            if duplicats.count() == 0 or any(
                [d.statut == ActeurStatus.ACTIF for d in duplicats]
            ):
                raise ValueError(f"Parent '{self.id}' should already be deleted")
            else:
                for d in duplicats:
                    d.parent = None
                    d.save()
                rev.delete()

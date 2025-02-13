"""
change_model to delete a parent acteur


"""

from data.models.change_models.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import RevisionActeur


class ChangeActeurDeleteAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_delete_as_parent"

    def validate(self):
        """If our overall acteur management logic is working correctly,
        we should not have to delete a parent here as:
         - we should first take care of its children (e.g. pointing to new parent)
         - consequently the parent should be automatically deleted (see PR1247)
        """
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if rev.exists():
            raise ValueError(
                f"Parent '{self.identifiant_unique}' should already be deleted"
            )

    def apply(self):
        self.validate()

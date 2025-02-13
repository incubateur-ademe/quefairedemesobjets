"""
change_model to update an acteur's parent


"""

from data.models.change_models.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, RevisionActeur


class ChangeActeurUpdateParentId(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_parent_id"

    def validate(self):
        """The parent we want to point the acteur to should exist,
        and the actuer should exist in base"""
        Acteur.objects.get(pk=self.identifiant_unique)
        return RevisionActeur.objects.get(pk=self.data.get("parent_id"))

    def apply(self):
        parent = self.validate()
        rev = RevisionActeur.objects.filter(pk=self.identifiant_unique)
        if not rev.exists():
            rev = RevisionActeur(identifiant_unique=self.identifiant_unique)
        else:
            rev = rev.first()
        rev.parent = parent  # type: ignore
        rev.save()  # type: ignore

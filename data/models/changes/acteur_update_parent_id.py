"""change model to update an acteur's parent"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, RevisionActeur


class ChangeActeurUpdateParentId(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_parent_id"

    def validate(self):
        # - The acteur MUST exist in base
        return Acteur.objects.get(pk=self.id)
        # - It's OK for acteur to not be in revision
        # - Can't test if parent exists as maybe it's to be created

    def apply(self):
        base = self.validate()
        # By the time we apply changes to update parent_ids, the
        # corresponding parents must exist
        parent = RevisionActeur.objects.get(pk=self.data["parent_id"])
        rev = RevisionActeur.objects.filter(pk=self.id)
        if not rev.exists():
            rev = RevisionActeur(
                identifiant_unique=self.id, acteur_type=base.acteur_type
            )
        else:
            rev = rev.first()
        rev.parent = parent  # type: ignore
        rev.save()  # type: ignore

"""Generic change model to update an acteur's data. If your use-case
is very specific (e.g. RGPD), create dedicated model for more clarity/reliability."""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur


class ChangeActeurUpdate(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update"

    def validate(self) -> Acteur:
        if not self.data:
            raise ValueError("Aucune donnée fournie")
        # The parent should already exist in revision or base
        # We tolerate absence from revision
        acteur = Acteur.objects.get(pk=self.id)
        return acteur

    def apply(self):
        acteur = self.validate()

        for key, value in self.data.items():
            setattr(acteur, key, value)
        acteur.save()

"""Generic change model to update an acteur's data. If your use-case
is very specific (e.g. RGPD), create dedicated model for more clarity/reliability."""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from data.models.changes.utils import data_reconstruct
from qfdmo.models import Acteur, RevisionActeur


class ChangeActeurUpdateData(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_data"

    def validate(self) -> Acteur | RevisionActeur:
        if not self.data:
            raise ValueError("No data provided")
        # The parent should already exist in revision or base
        # We tolerate absence from revision
        result = RevisionActeur.objects.filter(pk=self.id).first()
        if not result:
            # But if not in revision, must be in base
            result = Acteur.objects.get(pk=self.id)
        return result

    def apply(self):
        acteur = self.validate()
        # If acteur is only in base, we need to create a revision
        if isinstance(acteur, Acteur):
            acteur = RevisionActeur(
                identifiant_unique=acteur.identifiant_unique,
                acteur_type=acteur.acteur_type,
            )
        data = data_reconstruct(RevisionActeur, self.data)
        for key, value in data.items():
            setattr(acteur, key, value)
        acteur.save()

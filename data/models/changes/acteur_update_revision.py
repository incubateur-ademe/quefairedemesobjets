"""Generic change model to update an acteur's data. If your use-case
is very specific (e.g. RGPD), create dedicated model for more clarity/reliability."""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, RevisionActeur


class ChangeActeurUpdateRevision(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_revision"

    def validate(self) -> Acteur | RevisionActeur:
        if not self.data:
            raise ValueError("Aucune donnée fournie")
        # The parent should already exist in revision or base
        # We tolerate absence from revision
        try:
            acteur = Acteur.objects.get(pk=self.id)
        except Acteur.DoesNotExist:
            try:
                # We need it to manage when it is a parent
                acteur = RevisionActeur.objects.get(pk=self.id)
            except RevisionActeur.DoesNotExist:
                raise ValueError(f"L'acteur cible {self.id} n'existe pas")
        return acteur

    def apply(self):
        acteur = self.validate()

        revision = (
            acteur.get_or_create_revision() if isinstance(acteur, Acteur) else acteur
        )

        for key, value in self.data.items():
            setattr(revision, key, value)
        revision.save()

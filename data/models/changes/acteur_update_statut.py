"""Change model to update an acteur's statut. We need a speciific change model because
the statut is updated in acteur and revisionacteur tables."""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, ActeurStatus, RevisionActeur


class ChangeActeurUpdateStatut(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_statut"

    def validate(self):
        if not self.data:
            raise ValueError("No data provided")

        if "statut" not in self.data:
            raise ValueError("No statut provided")

        if self.data["statut"] not in ActeurStatus.values:
            raise ValueError(f"Invalid statut: {self.data['statut']}")

    def apply(self):
        instances = self.validate()

        instances: list[Acteur | RevisionActeur] = [Acteur.objects.get(pk=self.id)]
        if revision := RevisionActeur.objects.filter(pk=self.id).first():
            instances.append(revision)

        for instance in instances:
            instance.statut = self.data["statut"]
            instance.save()

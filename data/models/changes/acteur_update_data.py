from dags.cluster.tasks.business_logic.misc.data_serialize_reconstruct import (
    data_reconstruct,
)
from data.models.changes.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import Acteur, RevisionActeur


class ChangeActeurUpdateData(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_update_data"

    def validate(self):
        # The parent should already exist
        if not self.data:
            raise ValueError("No data provided")
        result = RevisionActeur.objects.filter(pk=self.id).first()
        if not result:
            result = Acteur.objects.get(pk=self.id)
        return result

    def apply(self):
        acteur = self.validate()
        if isinstance(acteur, Acteur):
            acteur = RevisionActeur(identifiant_unique=acteur.identifiant_unique)
        data = data_reconstruct(RevisionActeur, self.data)
        for key, value in data.items():
            setattr(acteur, key, value)
        acteur.save()

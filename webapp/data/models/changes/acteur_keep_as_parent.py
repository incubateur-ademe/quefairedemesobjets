from data.models.changes.acteur_abstract import ChangeActeurAbstract
from data.models.changes.utils import data_reconstruct
from qfdmo.models import RevisionActeur


class ChangeActeurKeepAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_keep_as_parent"

    def validate(self):
        # The parent should already exist
        return RevisionActeur.objects.get(pk=self.id)

    def apply(self):
        rev = self.validate()
        # No need to update if no data provided
        data = self.data
        if data:
            data = data_reconstruct(RevisionActeur, data)
            for key, value in data.items():
                setattr(rev, key, value)
            rev.save_as_parent()

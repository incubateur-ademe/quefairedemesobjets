"""
change_model to create a parent acteur


"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from data.models.changes.utils import parent_data_prepare
from qfdmo.models import ActeurStatus, RevisionActeur


class ChangeActeurCreateAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_create_as_parent"

    # Whilst creating as parent we allow enriching its data
    data: dict = {}

    def validate(self):
        """The parent shouldn't already exist"""
        rev = RevisionActeur.objects.filter(identifiant_unique=self.id)
        if rev.exists():
            raise ValueError(f"Parent to create '{self.id}' already exists")

    def apply(self):
        self.validate()
        data = self.data
        data.update({"identifiant_unique": self.id})
        data = parent_data_prepare(data)
        self.data["statut"] = ActeurStatus.ACTIF
        rev = RevisionActeur(**self.data)
        rev.save_as_parent()

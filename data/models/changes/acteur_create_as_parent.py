"""change model to create a parent acteur"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from data.models.changes.utils import data_reconstruct
from qfdmo.models import ActeurStatus, RevisionActeur


class ChangeActeurCreateAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_create_as_parent"

    # Whilst creating as parent we allow enriching its data
    data: dict = {}

    def validate(self):
        """The parent shouldn't already exist"""
        print(f"ChangeActeurCreateAsParent.validate: {self.id=} {self.data=}")
        rev = RevisionActeur.objects.filter(identifiant_unique=self.id)
        if rev.exists():
            raise ValueError(f"Parent to create '{self.id}' already exists")

    def apply(self):
        self.validate()
        data = self.data
        data.update({"identifiant_unique": self.id})
        data = data_reconstruct(RevisionActeur, data)
        data["statut"] = ActeurStatus.ACTIF
        rev = RevisionActeur(**data)
        rev.save_as_parent()

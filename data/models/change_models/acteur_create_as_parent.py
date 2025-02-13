"""
change_model to create a parent acteur


"""

from data.models.change_models.acteur_abstract import ChangeActeurAbstract
from qfdmo.models import RevisionActeur


class ChangeActeurCreateAsParent(ChangeActeurAbstract):
    @classmethod
    def name(cls) -> str:
        return "acteur_create_as_parent"

    def validate(self):
        """The parent shouldn't already exist"""
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if rev.exists():
            raise ValueError(
                f"Parent to create '{self.identifiant_unique}' already exists"
            )

    def apply(self):
        self.validate()
        rev = RevisionActeur(identifiant_unique=self.identifiant_unique)
        rev.save_as_parent()

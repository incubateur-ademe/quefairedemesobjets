"""change model to create a parent acteur"""

from data.models.changes.acteur_abstract import ChangeActeurAbstract
from data.models.changes.utils import data_reconstruct
from qfdmo.models import ActeurStatus, RevisionActeur
from qfdmo.models.acteur import RevisionPerimetreADomicile


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
        data = data_reconstruct(RevisionActeur, data)
        data["statut"] = ActeurStatus.ACTIF

        # Get perimetre_adomiciles and remove it from data before create RevisonActeur
        perimetre_adomiciles = data.get("perimetre_adomiciles", [])
        if "perimetre_adomiciles" in data:
            del data["perimetre_adomiciles"]

        # Create RevisionActeur as parent
        rev = RevisionActeur(**data)
        rev.save_as_parent()

        # Create perimetre_adomicilesonce RevisionActeur is created
        for perimetre in perimetre_adomiciles:
            RevisionPerimetreADomicile.objects.create(
                acteur=rev, type=perimetre["type"], valeur=perimetre["value"]
            )

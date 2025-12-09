from django.contrib.gis.geos import Point

from data.models.apply_models.abstract_apply_model import AbstractApplyModel
from qfdmo.models.acteur import Acteur, RevisionActeur


class SourceApplyModel(AbstractApplyModel):

    @classmethod
    def name(cls) -> str:
        return "SourceApplyModel"

    def validate(self) -> Acteur | RevisionActeur:
        """validate will raise an error if the data is invalid"""
        acteur = self.acteur_model.objects.filter(
            identifiant_unique=self.identifiant_unique
        ).first()
        if "latitude" in self.data and "longitude" in self.data:
            self.data["location"] = Point(
                float(self.data["longitude"]), float(self.data["latitude"])
            )
            del self.data["latitude"]
            del self.data["longitude"]
        if not acteur:
            acteur = self.acteur_model(
                **self.data,
            )
        else:
            for key, value in self.data.items():
                setattr(acteur, key, value)
        acteur.full_clean()
        return acteur

    def apply(self):
        """Apply the data updates to the acteur"""
        acteur = self.validate()
        acteur.save()

from data.models.apply_models.abstract_apply_model import AbstractApplyModel
from data.models.utils import data_latlong_to_location
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
        if not acteur:
            acteur = self.acteur_model(
                **data_latlong_to_location(self.data),
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

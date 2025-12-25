import json

from django.db import models

from data.models.apply_models.abstract_apply_model import AbstractApplyModel
from data.models.utils import data_latlong_to_location
from qfdmo.models.acteur import (
    Acteur,
    PerimetreADomicile,
    PropositionService,
    RevisionActeur,
    RevisionPerimetreADomicile,
    RevisionPropositionService,
)
from qfdmo.models.action import Action
from qfdmo.models.categorie_objet import SousCategorieObjet


class SourceApplyModel(AbstractApplyModel):
    @classmethod
    def name(cls) -> str:
        return "SourceApplyModel"

    def _set_acteur_linked_objects(self, acteur: Acteur | RevisionActeur, data: dict):
        for key, value in data.items():
            if key.endswith("_code"):
                # - source_code
                # - acteur_type_code
                field_name = key.removesuffix("_code")
                # Get the ForeignKey field from model metadata
                field = acteur._meta.get_field(field_name)

                # Verify it's a ForeignKey and set relationship
                if isinstance(field, models.ForeignKey):
                    related_model_class = field.related_model
                    related_instance = related_model_class.objects.get(code=value)
                    setattr(acteur, field_name, related_instance)
                else:
                    raise ValueError(
                        f"fount {field_name}_code key but Field {field_name} is not"
                        " a ForeignKey"
                    )
            elif key == "proposition_service_codes":
                if isinstance(acteur, RevisionActeur):
                    propositon_service_class = RevisionPropositionService
                else:
                    propositon_service_class = PropositionService
                proposition_service_values = json.loads(value.replace("'", '"'))
                acteur.proposition_services.all().delete()
                for proposition_service in proposition_service_values:
                    proposition_service_instance = (
                        propositon_service_class.objects.create(
                            action=Action.objects.get(
                                code=proposition_service["action"]
                            ),
                            acteur=acteur,
                        )
                    )
                    for sous_categorie_code in proposition_service["sous_categories"]:
                        proposition_service_instance.sous_categories.add(
                            SousCategorieObjet.objects.get(code=sous_categorie_code)
                        )
            elif key == "perimetre_adomicile_codes":
                if isinstance(acteur, RevisionActeur):
                    perimetre_adomicile_class = RevisionPerimetreADomicile
                else:
                    perimetre_adomicile_class = PerimetreADomicile
                perimetre_adomicile_values = json.loads(value.replace("'", '"'))
                acteur.perimetre_adomiciles.all().delete()
                for perimetre_adomicile in perimetre_adomicile_values:
                    perimetre_adomicile_class.objects.create(
                        type=perimetre_adomicile["type"],
                        valeur=perimetre_adomicile["valeur"],
                        acteur=acteur,
                    )
            elif key.endswith("_codes"):
                # - label_codes
                # - acteur_service_codes
                field_name = key.removesuffix("_codes") + "s"
                linked_objects = getattr(acteur, field_name)
                linked_object_class = acteur._meta.get_field(field_name).related_model
                linked_object_values = json.loads(value.replace("'", '"'))
                linked_objects.clear()
                for linked_object in linked_object_values:
                    linked_objects.add(
                        linked_object_class.objects.get(code=linked_object)
                    )

    def validate(self) -> Acteur | RevisionActeur:
        """validate will raise an error if the data is invalid"""
        acteur = self.acteur_model.objects.filter(
            identifiant_unique=self.identifiant_unique
        ).first()
        data = data_latlong_to_location(self.data)
        if not acteur:
            acteur = self.acteur_model(
                **data_latlong_to_location(self.data),
            )
        else:
            for key, value in data.items():
                setattr(acteur, key, value)
        acteur.full_clean()
        return acteur

    def apply(self):
        """Apply the data updates to the acteur"""
        acteur = self.validate()
        acteur.save()
        self._set_acteur_linked_objects(acteur, self.data)

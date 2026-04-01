import json
from abc import abstractmethod

from data.models.comparison_table import ComparisonTable
from data.models.suggestion import SuggestionGroupe
from data.models.utils import prepare_acteur_data_with_location
from django.db import models as django_models
from pydantic import BaseModel, ConfigDict
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


class SuggestionGroupeType(BaseModel):
    """Abstract base class for SuggestionGroupe type handlers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    suggestion_groupe: SuggestionGroupe
    display_tab: bool = False

    @abstractmethod
    def from_suggestion_groupe(
        self, suggestion_groupe: SuggestionGroupe
    ) -> "SuggestionGroupeType":
        pass

    @abstractmethod
    def to_comparison_table(self) -> ComparisonTable:
        pass

    @abstractmethod
    def apply(self):
        pass

    @staticmethod
    def _apply_one(
        acteur_model: type[Acteur | RevisionActeur],
        identifiant_unique: str,
        data: dict,
    ) -> Acteur | RevisionActeur:

        try:
            acteur = acteur_model.objects.get(identifiant_unique=identifiant_unique)
        except acteur_model.DoesNotExist:
            acteur = None

        prepared = prepare_acteur_data_with_location(data)
        if "identifiant_unique" not in prepared:
            prepared["identifiant_unique"] = identifiant_unique

        if not acteur:
            acteur = acteur_model(**prepared)
        else:
            for key, value in prepared.items():
                setattr(acteur, key, value)

        SuggestionGroupeType._set_foreign_key_from_code(acteur, data)
        acteur.full_clean()
        acteur.save()
        return acteur

    @staticmethod
    def _set_foreign_key_from_code(acteur: Acteur | RevisionActeur, data: dict):

        for key, value in data.items():
            if key.endswith("_code"):
                field_name = key.removesuffix("_code")
                field = acteur._meta.get_field(field_name)
                if isinstance(field, django_models.ForeignKey):
                    related_model_class = field.related_model
                    related_instance = related_model_class.objects.get(code=value)
                    setattr(acteur, field_name, related_instance)
                else:
                    raise ValueError(
                        f"fount {field_name}_code key but Field {field_name} is not"
                        " a ForeignKey"
                    )

    @staticmethod
    def _set_acteur_linked_objects(acteur: Acteur | RevisionActeur, data: dict):

        for key, value in data.items():
            if key == "proposition_service_codes":
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
                field_name = key.removesuffix("_codes") + "s"
                linked_objects = getattr(acteur, field_name)
                linked_object_class = acteur._meta.get_field(field_name).related_model
                linked_object_values = json.loads(value.replace("'", '"'))
                linked_objects.clear()
                for linked_object in linked_object_values:
                    linked_objects.add(
                        linked_object_class.objects.get(code=linked_object)
                    )

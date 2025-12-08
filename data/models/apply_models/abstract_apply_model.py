"""change model to use as template for acteur changes"""

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel

from qfdmo.models.acteur import Acteur, BaseActeur, RevisionActeur

ACTEUR_MODEL = {
    "Acteur": Acteur,
    "RevisionActeur": RevisionActeur,
}


class AbstractApplyModel(BaseModel, ABC):
    """Abstract class to apply a model to an acteur"""

    identifiant_unique: str
    order: int = 0
    acteur_model: Type[BaseActeur] = ACTEUR_MODEL["Acteur"]
    data: dict = {}

    @classmethod
    def name(cls) -> str:
        # Return a name in snake_case format
        raise NotImplementedError("Method must be implemented")

    @abstractmethod
    def validate(self):
        # Method called to validate the data
        # - either as standalone when we prepare suggestions
        # - or automatically as part of apply
        raise NotImplementedError("Method must be implemented")

    @abstractmethod
    def apply(self):
        # Method called to make the change effective
        self.validate()
        raise NotImplementedError("Method must be implemented")

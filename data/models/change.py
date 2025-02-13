"""
💡 QUOI:
Modèles pydantic liés aux changements atomiques
apportés par les suggestions

🎯 POURQUOI:
 - pydantic nous permet de découpler les suggestions
   de la DB
 - mais la méthode .apply() nous permet d'utiliser
    les modèles qfdmo pour appliquer les changements
    au moment voulu

🚧 COMMENT APPLIQUER UN CHANGEMENT:
 - Faire passer la donner de suggestion dans le modèle
 - Appeler .apply()


🧊 MODELISATION DES SUGGESTIONS:
On pourrait stocker les changements des suggestions
sous forme modélisée:
 🟢 avantage: prêt a l'emploi (plus qu'a récupérer et faire apply
 au moment de l'approbation), mais au final gain marginal
 🔴 incovénient: les suggestions en DB deviennent dépendentes
 des modèles, si les modèles changent on perd potentiellement
 les suggestions OU il faut en faire des migrations

Pour l'instant on voit que 🔴>>🟢 et on décide de:
 1) suggestion: on utilise le modèle UNIQUEMENT pour la validation,
    mais on stoque la donnée non modèlisée
 2) changement: on rejoue la donnée dans le modèle et on applique .apply()

Notes:
- Définir un modèle de changement dontles autres héritent
- Stocker l'ordre des changements par type
- Centralisation la résolution du template de la cellule changement dans l'admin dans
chaque modèle pydantic
"""

from pydantic import BaseModel, Field, model_validator

from data.models.change_models import CHANGE_MODELS

MODEL_NAMES = list(CHANGE_MODELS.keys())

# -----------------------------
# Optional namespace convenience columns
# -----------------------------
# Columns prefixed with "change_" namespace so they can be
# used to prepare suggestions inside dataframes without causing
# conflicts (ex: in clustering we can attach those columns to clusters)
# You do NOT HAVE to use those, as long as you provide
# a final suggestion which fields match that of SuggestionChange
COL_CHANGE_MODEL_NAME = "change_model_name"
COL_CHANGE_ORDER = "change_order"
COL_CHANGE_REASON = "change_reason"
COL_CHANGE_MODEL_PARAMS = "change_data"
COL_ENTITY_TYPE = "entity_type"


class SuggestionChange(BaseModel):
    """Model for 1 suggestion change, a suggestion
    can be composed of 1 or more changes"""

    # Some suggestions are composed of multiple changes
    # which MUST be executed in a specific order (ex: clustering
    # we need to create a parent before attaching children to it)
    order: int = Field(ge=1)
    # Debug only, but we should provide a clear explanation
    # as to why we're doing a change
    reason: str = Field(min_length=5)
    # Name of the pydantic model we will use to make the change
    # Reference to change_models/{my_class}.py/{MyClass}.name()
    name: str = Field(min_length=1)
    # The params passed to the pydantic model
    model_params: dict = {}

    @model_validator(mode="after")  # type: ignore
    def check_model(self) -> None:
        # name must be in the list of available models
        name = self.name
        if name not in MODEL_NAMES:
            raise ValueError(f"Invalid name: {name}, must be in {MODEL_NAMES}")

        # Validate the given data when constructing the suggestion.
        # This allows catching problems when preparing suggestions
        # and not wait until they are approved and applied to find out
        model = CHANGE_MODELS[name]
        model(**self.model_params).validate()

        # Required by Pydantic
        # UserWarning: A custom validator is returning a value other than `self`
        return self  # type: ignore

    def apply(self):
        model = CHANGE_MODELS[self.name]
        # Models are constructed to call validate() within apply()
        model(**self.model_params).apply()


# -----------------------------
# 0) entity_type
# -----------------------------
ENTITY_ACTEUR_REVISION = "acteur_revision"
ENTITY_ACTEUR_DISPLAYED = "acteur_displayed"

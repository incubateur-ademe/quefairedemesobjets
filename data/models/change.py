"""
💡 WHAT:
Pydantic model to define 1 suggestion change
(a suggestion being composed of 1 or more changes)

So we have:
Suggestion.suggestion["changes"] = list[SuggestionChange]

TODO: I propose to rename Suggestion.suggestion to .changes
to have Suggestion.changes = list[SuggestionChange], whatever
is currently in .suggestion and not destined to .changes should
be moved to some metadata field

🎯 WHY:
The change being nested within a suggestion field,
we don't want to use Django models to validate the data
(DB model = Django, Non-DB Models = Pydantic)

🔢 HOW:
If we step back and look at the bigger picture:
 - we start with a Suggestion
 - on which we do Suggestion.apply()
 - which does:

changes = self.suggestion["changes"]
changes.sort(key=lambda x: x["order"])
for change in changes:
     SuggestionChange(**change).apply()
"""

import logging

from pydantic import BaseModel, Field, model_validator

# This is where we store individual change models
# referenced by SuggestionChange.model_name
from data.models.changes import CHANGE_MODELS

logger = logging.getLogger(__name__)

# To validate chosen model names
MODEL_NAMES = list(CHANGE_MODELS.keys())

# -----------------------------
# Optional/convenience constants
# -----------------------------
# Columns prefixed with "change_" namespace so they can be
# used to prepare suggestions inside data pipelines df without causing
# conflicts (ex: in clustering we can attach those columns to clusters)
COL_CHANGE_NAMESPACE = "change_"
COL_CHANGE_ORDER = f"{COL_CHANGE_NAMESPACE}order"
COL_CHANGE_REASON = f"{COL_CHANGE_NAMESPACE}reason"
COL_CHANGE_MODEL_NAME = f"{COL_CHANGE_NAMESPACE}model_name"
COL_CHANGE_MODEL_PARAMS = f"{COL_CHANGE_NAMESPACE}model_params"
COL_CHANGE_ENTITY_TYPE = f"{COL_CHANGE_NAMESPACE}entity_type"

# -----------------------------
# Entity types
# -----------------------------
# Defining entity types serves several purposes:
# - ℹ️ Show useful info in both Airflow/Django UI
#   (e.g. explain to métier whether we are working on an
#    acteur that's in base or revision)
# - ✅ Validate intention vs. reality (e.g. if we thought
#    we were dealing with an acteur in base but are using
#    methods for acteurs which must be in revision)
ENTITY_ACTEUR_BASE = "acteur_base"
ENTITY_ACTEUR_REVISION = "acteur_revision"
ENTITY_ACTEUR_DISPLAYED = "acteur_displayed"
ENTITY_ACTEUR_TO_CREATE = "acteur_to_create"
ENTITY_TYPES = [
    ENTITY_ACTEUR_BASE,
    ENTITY_ACTEUR_REVISION,
    ENTITY_ACTEUR_DISPLAYED,
    ENTITY_ACTEUR_TO_CREATE,
]


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
    # The type of entity we're changing (notably needed in clustering
    # as acteurs are scattered across 3 state tables)
    entity_type: str
    # Name of the pydantic model we will use to make the change
    # Reference to change_models/{my_class}.py/{MyClass}.name()
    model_name: str
    # The params passed to the pydantic model
    model_params: dict = {}

    @model_validator(mode="after")  # type: ignore
    def check_model(self) -> None:
        entity_type = self.entity_type
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Invalid {entity_type=}, must be in {ENTITY_TYPES=}")

        # name must be in the list of available models
        model_name = self.model_name
        if model_name not in MODEL_NAMES:
            raise ValueError(f"Invalid {model_name=}, must be in {MODEL_NAMES}")

        # Validate the given data when constructing the suggestion.
        # This allows catching problems when preparing suggestions
        # and not wait until they are approved and applied to find out
        Model = CHANGE_MODELS[model_name]
        Model(**self.model_params).validate()

        # Required by Pydantic
        # UserWarning: A custom validator is returning a value other than `self`
        return self  # type: ignore

    def apply(self):
        order = self.order
        reason = self.reason
        model_name = self.model_name
        model_params = self.model_params
        Model = CHANGE_MODELS[model_name]
        info = f"{order=} {reason=} {model_name=} {model_params=}"
        try:
            Model(**model_params).apply()
            logger.info(f"🟢 SuggestionChange.apply() SUCCESS on {info}")
        except Exception as e:
            logger.error(f"🔴 SuggestionChange.apply() ERROR {e} on {info}")
            raise e

"""Configuration model for the ML-deduplication DAG"""

from ml_deduplication.config.constants import FIELDS_PROTECTED
from pydantic import BaseModel, field_validator, model_validator
from utils.airflow_params import airflow_params_dropdown_selected_to_ids


class MLDeduplicationConfig(BaseModel):
    # ---------------------------------------
    # Champs de base
    # ---------------------------------------
    # Les champs qu'on s'attend à retrouver
    # dans les params airflow: on les consèrve
    # dans l'ordre de la UI Airflow, ce qui veut
    # dire qu'on ne peut pas mélanger valeurs par défaut
    # et valeurs obligatoires, voir section validation
    # pour toutes les règles
    dry_run: bool

    # SELECTION ACTEURS
    # La sélection des acteurs est réutilisée telle quelle par rapport
    # au DAG de clustering: elle définit le pool d'acteurs qu'on va donner
    # à l'inférence ML (via une vue temporaire).
    include_sources: list[str]
    include_acteur_types: list[str]

    # DEDUP
    # Réutilisé tel quel pour l'enrichissement des parents après inférence.
    dedup_enrich_fields: list[str]
    dedup_enrich_exclude_sources: list[str]
    dedup_enrich_exclude_source_ids: list[int]  # to calculate from above
    dedup_enrich_priority_sources: list[str]
    dedup_enrich_priority_source_ids: list[int]  # to calculate from above
    dedup_enrich_keep_empty: bool
    dedup_enrich_keep_parent_data_by_default: bool

    # ML INFERENCE
    # Vue/table source du pool d'acteurs donnée à l'inférence. Si vide,
    # on crée une vue temporaire à partir de la sélection acteurs.
    acteurs_table: str | None
    # Base name of the DB tables written by the inference:
    # <output_table>_clusters et <output_table>_predictions.
    output_table: str
    # Image de l'inférence + paramètres de run.
    image_ref: str
    model_threshold: float | None
    linkage_column: str | None
    split_by_departement: bool

    # LOCAL DEV
    # Si True, on n'utilise pas d'instance Scaleway: l'inférence tourne
    # localement avec docker (voir scripts d'infrastructure).
    run_locally: bool = False
    # Nombre max d'acteurs à sélectionner pour l'inférence (LIMIT). Vide = tous.
    limit_acteurs: int | None = None

    # ---------------------------------------
    # Listings & Mappings
    # ---------------------------------------
    # On fait la distinction entre les champs meta
    # qu'on ne souhaite pas transformer
    fields_protected: list[str]
    # Et les champs data qui peuvent être transformés
    # (ex: normalisation). Dans la validation de config
    # on vient enrichir cette liste avec tous les champs
    # sélectionnés par l'utilisateur du DAG Airflow
    fields_transformed: list[str]
    # Tous les champs data (utilisé pour lire le pool d'acteurs complet).
    fields_all: list[str]
    # Ajouter les mappings à la config facilite le debug
    # et évite d'avoir à faire des requêtes DB plusieurs fois
    mapping_sources: dict[str, int]
    mapping_acteur_types: dict[str, int]

    # ---------------------------------------
    # Champs calculés
    # ---------------------------------------
    # A partir des champs de base + logique métier
    # + valeurs de la base de données
    # Conversion des codes en ids
    include_source_ids: list[int]
    include_acteur_type_ids: list[int]

    # ---------------------------------------
    # Validation
    # ---------------------------------------
    # Champs isolés
    @field_validator("dry_run", mode="before")
    def check_dry_run(cls, v):
        if v is None:
            raise ValueError("dry_run à fournir")
        return v

    @field_validator("acteurs_table", mode="before")
    def check_acteurs_table(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("limit_acteurs", mode="before")
    def check_limit_acteurs(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v

    @field_validator("output_table", mode="before")
    def check_output_table(cls, v):
        if not v or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("output_table à fournir")
        return v

    # Logique multi-champs
    @model_validator(mode="before")
    def check_model(cls, values):
        # Fields with [] as default
        optionals_lists_default_empty = [
            "dedup_enrich_exclude_sources",
        ]
        for k in optionals_lists_default_empty:
            if values.get(k) is None:
                values[k] = []

        # SOURCE CODES
        # Si aucun code source fourni alors on inclut toutes les sources
        if not values.get("include_sources"):
            values["include_sources"] = []
            values["include_source_ids"] = list(values["mapping_sources"].values())
        else:
            # Sinon on résout les codes sources en ids à partir de la sélection
            values["include_source_ids"] = airflow_params_dropdown_selected_to_ids(
                mapping_ids_by_codes=values["mapping_sources"],
                dropdown_selected=values["include_sources"],
            )

        # ACTEUR TYPE CODES
        if not values.get("include_acteur_types"):
            raise ValueError("Au moins un type d'acteur doit être sélectionné")
        values["include_acteur_type_ids"] = airflow_params_dropdown_selected_to_ids(
            mapping_ids_by_codes=values["mapping_acteur_types"],
            dropdown_selected=values["include_acteur_types"],
        )

        # Constructing a list of fields to transform from all the
        # data fields (the inference handles normalization itself, so we
        # read the full acteur pool without transforming anything here).
        values["fields_protected"] = FIELDS_PROTECTED
        values["fields_all"] = values.get("fields_all") or []
        values["fields_transformed"] = list(
            set(values["fields_all"]) - set(FIELDS_PROTECTED)
        )

        # DEDUP
        values["dedup_enrich_exclude_source_ids"] = (
            airflow_params_dropdown_selected_to_ids(
                mapping_ids_by_codes=values["mapping_sources"],
                dropdown_selected=values["dedup_enrich_exclude_sources"],
            )
        )
        values["dedup_enrich_priority_source_ids"] = (
            airflow_params_dropdown_selected_to_ids(
                mapping_ids_by_codes=values["mapping_sources"],
                dropdown_selected=values["dedup_enrich_priority_sources"],
            )
        )

        return values

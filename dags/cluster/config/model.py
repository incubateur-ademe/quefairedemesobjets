from pydantic import BaseModel, Field, field_validator, model_validator
from utils.airflow_params import airflow_params_dropdown_selected_to_ids


class ClusterConfig(BaseModel):

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
    include_source_codes: list[str]
    include_acteur_type_codes: list[str]
    include_only_if_regex_matches_nom: str | None
    include_if_all_fields_filled: list[str]
    exclude_if_any_field_filled: list[str]
    normalize_fields_basic: list[str]
    normalize_fields_no_words_size1: list[str]
    normalize_fields_no_words_size2_or_less: list[str]
    normalize_fields_no_words_size3_or_less: list[str]
    normalize_fields_order_unique_words: list[str]
    cluster_intra_source_is_allowed: bool
    cluster_fields_exact: list[str]
    cluster_fields_fuzzy: list[str]
    cluster_fuzzy_threshold: float = Field(0.5, ge=0, le=1)

    # ---------------------------------------
    # Listings & Mappings
    # ---------------------------------------
    fields_used: list[str]
    fields_all: list[str]
    mapping_source_ids_by_codes: dict[str, int]
    mapping_acteur_type_ids_by_codes: dict[str, int]

    # ---------------------------------------
    # Champs calculés
    # ---------------------------------------
    # A partir des champs de base + logique métier
    # + valeurs de la base de données
    # Conversion des codes en ids
    include_source_ids: list[int]
    include_acteur_type_ids: list[int]
    # Champs sur lesquels on sépare les clusters
    cluster_fields_separate: list[str]

    # ---------------------------------------
    # Validation
    # ---------------------------------------
    # Champs isolés
    @field_validator("dry_run", mode="before")
    def check_dry_run(cls, v):
        if v is None:
            raise ValueError("dry_run à fournir")
        return v

    @field_validator("cluster_intra_source_is_allowed", mode="before")
    def check_cluster_intra_source_is_allowed(cls, v):
        if v is None:
            return False
        return v

    @field_validator("exclude_if_any_field_filled", mode="before")
    def check_exclude_if_any_field_filled(cls, v):
        if v is None:
            return []
        return v

    # Logique multi-champs
    @model_validator(mode="before")
    def check_model(cls, values):

        # SOURCE CODES
        # Si aucun code source fourni alors on inclut toutes les sources
        if not values.get("include_source_codes"):
            values["include_source_codes"] = []
            values["include_source_ids"] = values[
                "mapping_source_ids_by_codes"
            ].values()
        else:
            # Sinon on résout les codes sources en ids à partir de la sélection
            values["include_source_ids"] = airflow_params_dropdown_selected_to_ids(
                mapping_ids_by_codes=values["mapping_source_ids_by_codes"],
                dropdown_selected=values["include_source_codes"],
            )

        # ACTEUR TYPE CODES
        if not values.get("include_acteur_type_codes"):
            raise ValueError("Au moins un type d'acteur doit être sélectionné")
        values["include_acteur_type_ids"] = airflow_params_dropdown_selected_to_ids(
            mapping_ids_by_codes=values["mapping_acteur_type_ids_by_codes"],
            dropdown_selected=values["include_acteur_type_codes"],
        )

        # ACTEUR TYPE vs. INTRA-SOURCE
        if (
            len(values["include_source_ids"]) == 1
            and not values["cluster_intra_source_is_allowed"]
        ):
            raise ValueError("1 source sélectionnée mais intra-source désactivé")

        # Par défaut on ne clusterise pas les acteurs d'une même source
        # sauf si intra-source est activé
        values["cluster_fields_separate"] = ["source_id"]
        if values["cluster_intra_source_is_allowed"]:
            values["cluster_fields_separate"] = []

        # Fields avec default []
        optionals = [
            "normalize_fields_basic",
            "normalize_fields_no_words_size1",
            "normalize_fields_no_words_size2_or_less",
            "normalize_fields_no_words_size3_or_less",
            "normalize_fields_order_unique_words",
        ]
        for k in optionals:
            if not values.get(k):
                values[k] = []

        # Liste UNIQUE des champs utilisés
        fields_used = ["source_id", "acteur_type_id", "identifiant_unique"]
        for k, v in values.items():
            if "fields" in k and k != "fields_all" and k != "source_id":
                fields_used.extend(v)
        values["fields_used"] = fields_used
        values["fields_used"] = list(set(fields_used))

        # Si aucun champ pour la normalisation basique = tous les champs
        # utilisés seront normalisés
        if values["normalize_fields_basic"]:
            values["normalize_fields_basic"] = values["fields_used"]

        return values

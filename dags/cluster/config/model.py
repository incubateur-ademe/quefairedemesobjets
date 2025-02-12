"""
Modèle pydantic pour gérer la configuration
du DAG de clustering des acteurs. On utilise bien
le terme "config" et pas seulement "params" car les
"params" de la UI Airflow sont une sous-partie de ce qui
créer la config finale.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from utils.airflow_params import airflow_params_dropdown_selected_to_ids

FIELDS_PROTECTED_ALL = [
    "source_id",
    "acteur_type_id",
    "identifiant_unique",
    "statut",
    "nombre_enfants",
]


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

    # SELECTION ACTEURS NON-PARENTS
    include_sources: list[str]
    include_acteur_types: list[str]
    include_only_if_regex_matches_nom: str | None
    include_if_all_fields_filled: list[str]
    exclude_if_any_field_filled: list[str]

    # SELECTION PARENTS EXISTANTS
    # Pas de champ source car par définition parents = 0 source
    # Pas de champ acteur type = on prend tous les acteur type ci-dessus
    include_parents_only_if_regex_matches_nom: str | None

    # NORMALISATION
    normalize_fields_basic: list[str]
    normalize_fields_no_words_size1: list[str]
    normalize_fields_no_words_size2_or_less: list[str]
    normalize_fields_no_words_size3_or_less: list[str]
    normalize_fields_order_unique_words: list[str]

    # CLUSTERING
    cluster_intra_source_is_allowed: bool
    cluster_fields_exact: list[str]
    cluster_fields_fuzzy: list[str]
    cluster_fuzzy_threshold: float = Field(0.5, ge=0, le=1)

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
        if not values.get("include_sources"):
            values["include_sources"] = []
            values["include_source_ids"] = values["mapping_sources"].values()
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

        """
        Logique supprimée le 2025-01-27 mais conservée pour référence:
        - depuis l'ajout des parents indépendants des sources
        via PR1265 on ne peut plus savoir si on héritera
        uniquement d'une seule source au moment de la config, donc on
        laisse passer au niveau de la sélection
        TODO: on pourrait scinder la config en plusieurs sous-config:
            - SelectionConfig
            - NormalizationConfig
            - ClusteringConfig
            - EnrichmentConfig
        Et ainsi avoir des validations plus fines à chaque étape
        # ACTEUR TYPE vs. INTRA-SOURCE
        if (
            len(values["include_source_ids"]) == 1
            and not values["cluster_intra_source_is_allowed"]
        ):
            raise ValueError("1 source sélectionnée mais intra-source désactivé")
        """

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

        # Construction de la liste des champs meta et data
        # qui permet à travers de la pipeline de faire la distinction
        # entre ce qu'on peut transformer car étant de la donnée (data)
        # et ce qu'on doit garder inchangé (meta)
        values["fields_protected"] = FIELDS_PROTECTED_ALL
        values["fields_transformed"] = []
        for k, v in values.items():
            # On enrichit la liste des champs data avec les champs
            # sélectionnés dans les différent paramètres de config
            # à condition qu'ils ne soient pas meta
            if "fields" in k and k != "fields_protected":
                values["fields_transformed"] += [
                    x for x in v if x not in FIELDS_PROTECTED_ALL
                ]
        values["fields_transformed"] = list(set(values["fields_transformed"]))

        # Si aucun champ pour la normalisation basique = tous les champs
        # data seront normalisés, pareil pour la norma d'ordre/unicité
        if not values["normalize_fields_basic"]:
            values["normalize_fields_basic"] = values["fields_transformed"]
        if not values["normalize_fields_order_unique_words"]:
            values["normalize_fields_order_unique_words"] = values["fields_transformed"]

        return values

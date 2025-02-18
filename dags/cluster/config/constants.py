# ---------------------------------------
# Django models
# ---------------------------------------
# "fields" is the terminology for Django models
# Protected fields are fields we don't want to
# transformed nor used for enrichment
FIELDS_PROTECTED = [
    "source_id",
    "acteur_type_id",
    "identifiant_unique",
    "statut",
    "nombre_enfants",
    "cree_le",
    "modifie_le",
    "commentaires",
    "action_principale_id",
    "identifiant_externe",
]

FIELDS_PARENT_DATA_EXCLUDED = [
    # Depending on contexte, foreign keys are sometimes
    # represented in their Django model form without _id
    "proposition_services",
    "source",
    "source_id",
    "statut",
    # TODO: we can't set cree_le consistently
    # (see test_data_serialize_reconstruct), thus
    # we exclude it for now (maybe solution is to compute)
    # it via a view from all children for each parent
    "cree_le",
    "modifie_le",
    "identifiant_unique",
    "identifiant_externe",
]

# ---------------------------------------
# Dataframe columns
# ---------------------------------------
# "columns" is the terminology for pandas dataframes
# Stores the data used for changes
COL_PARENT_DATA_NEW = "parent_data_new"

# TODO: it would be better to have this as _new, more
# consistent with above AND more importantly: we don't
# touch what's current, we add columns for what's new
COL_PARENT_ID_BEFORE = "parent_id_before"
# TODO: to help us debug the original index within dfs
# as they go through the clustering process
COL_INDEX_SRC = "__index_src"

# ---------------------------------------
# Entity types
# ---------------------------------------
# This does NOT provide functionality but is
# used to help with displaying results

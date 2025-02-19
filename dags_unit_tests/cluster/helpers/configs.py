"""
Various Configurations used for the tests

We represent the confs in dict format because:
 - ConfigModel might contain DB validation (e.g. verify given sources exist)
 - We can more easily create custom configs by tweaking others' dict
"""

from airflow.utils.dates import days_ago

# So Airflow doesn't wait for the task's date to occur
DATE_IN_PAST = days_ago(2)

CONF_BASE_DICT = {
    "dry_run": True,
    "include_sources": ["ecopae (id=252)", "cyclevia (id=90)"],
    "include_acteur_types": ["decheterie (id=7)"],
    "include_only_if_regex_matches_nom": "dechett?erie",
    "include_parents_only_if_regex_matches_nom": "parent",
    "include_if_all_fields_filled": ["code_postal"],
    "exclude_if_any_field_filled": None,
    "normalize_fields_basic": None,
    "normalize_fields_no_words_size1": ["nom"],
    "normalize_fields_no_words_size2_or_less": ["nom"],
    "normalize_fields_no_words_size3_or_less": ["nom"],
    "normalize_fields_order_unique_words": None,
    "cluster_intra_source_is_allowed": False,
    "cluster_fields_exact": ["code_postal", "ville"],
    "cluster_fields_fuzzy": ["nom", "adresse"],
    "cluster_fuzzy_threshold": 0.5,
    "dedup_enrich_fields": ["nom", "siret", "email"],
    "dedup_enrich_exclude_sources": ["ecopae (id=252)"],
    "dedup_enrich_priority_sources": ["cyclevia (id=90)"],
    "dedup_enrich_keep_empty": False,
    # These mappings are passed by the config_create task
    # and should contain sources & acteur types given in conf
    "mapping_sources": {"ecopae": 252, "cyclevia": 90},
    "mapping_acteur_types": {"decheterie": 7},
}

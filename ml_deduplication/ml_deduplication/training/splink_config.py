"""Splink configuration module.

Defines comparison and blocking rule configurations mapped from our dedupe variable
configs (mandatory, restricted, full). Uses 2-digit code postal prefix for blocking
to handle errors in postal codes. High precision thresholds to minimize false positives.
"""

import logging

import numpy as np
import splink.comparison_library as cl
from splink import SettingsCreator

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Blocking rules                                                             #
# --------------------------------------------------------------------------- #
# Uses LEFT(code_postal, 2) to handle errors in postal codes.             #
# High-precision blocks prefer exact name match; broader blocks accept fuzzy   #
# matches but sacrifice some recall for precision (user's stated objective).   #
# --------------------------------------------------------------------------- #
BUSINESS_RULES_FRAGMENT = """AND
    (
        (
            (l.acteur_type_id = r.acteur_type_id)
            OR (l.acteur_type_id = 4 AND r.acteur_type_id = 3)
            OR (l.acteur_type_id = 3 AND r.acteur_type_id = 4)
        )
        AND (coalesce(l.source_id,-1)!=coalesce(r.source_id,-2))
    )"""

BLOCKING_CODE_POSTAL_2DIGITS = (
    "(substr(l.code_postal,1,2) == substr(r.code_postal,1,2))"
)

BLOCKING_SIREN_STRICT = """
(l.siren == r.siren)
"""

BLOCKING_GEO_DISTANCE = """
(
ST_DISTANCE_SPHEROID(
    ST_Point(l.latitude,l.longitude),
    ST_Point(r.latitude,r.longitude)
    ) < 30000
)
"""

BLOCKING_SIREN = "l.siren IS NOT NULL AND l.siren = r.siren"


# --------------------------------------------------------------------------- #
#  Comparison definitions per tier                                            #
# --------------------------------------------------------------------------- #
SPLINK_SETTINGS = SettingsCreator(
    link_type="dedupe_only",
    comparisons=[
        cl.NameComparison(
            "nom_clean", jaro_winkler_thresholds=[0.99, 0.95, 0.92, 0.88, 0.8, 0.7]
        ),
        cl.CosineSimilarityAtThresholds(
            "adresse_clean_vector",
            np.concat([np.array([0.99]), np.arange(0.95, 0.45, -0.05)]),
        ),
        cl.JaroWinklerAtThresholds("ville", [0.99, 0.98, 0.95, 0.90]),
        cl.EmailComparison("email"),
        cl.ExactMatch("siren"),
        cl.ExactMatch("siret"),
        cl.ExactMatch("telephone"),
        cl.ExactMatch("naf_principal"),
        cl.CustomComparison(
            output_column_name="code_postal_and_code_insee",
            comparison_levels=[
                {
                    "sql_condition": "(code_postal_l IS NULL OR code_postal_r IS NULL) AND (code_commune_insee_l is null OR code_commune_insee_r is null)",
                    "label_for_charts": "code_postal is NULL",
                    "is_null_level": True,
                },
                {
                    "sql_condition": "code_commune_insee_l == code_commune_insee_r",
                    "label_for_charts": "code commune equals",
                },
                {
                    "sql_condition": "code_postal_l == code_postal_r",
                    "label_for_charts": "code postal equals",
                },
                {
                    "sql_condition": "code_postal_l[1:2] == code_postal_r[1:2]",
                    "label_for_charts": "code postal department equals",
                },
                {"sql_condition": "ELSE", "label_for_charts": "All other comparisons"},
            ],
            comparison_description="ExactMatch",
        ),
        {
            "output_column_name": "location_custom",
            "comparison_levels": [
                {
                    "sql_condition": '"latitude_l" IS NULL OR "latitude_r" IS NULL OR "longitude_l" IS NULL OR "longitude_r" IS NULL',
                    "label_for_charts": "location is NULL",
                    "is_null_level": True,
                },
                *[
                    {
                        "sql_condition": f"ST_DISTANCE_SPHEROID(ST_Point(latitude_l,longitude_l),ST_Point(latitude_r,longitude_r)) < {e}",
                        "label_for_charts": f"location within {e}m",
                    }
                    for e in [5, 25, 50, 100, 500, 1000, 5000]
                ],
                {"sql_condition": "ELSE", "label_for_charts": "All other comparisons"},
            ],
            "comparison_description": "ExactMatch",
        },
    ],
    blocking_rules_to_generate_predictions=[
        BLOCKING_CODE_POSTAL_2DIGITS + BUSINESS_RULES_FRAGMENT,
        BLOCKING_SIREN_STRICT + BUSINESS_RULES_FRAGMENT,
        BLOCKING_GEO_DISTANCE + BUSINESS_RULES_FRAGMENT,
    ],  # type: ignore
    retain_intermediate_calculation_columns=True,
    unique_id_column_name="entity_id",
    additional_columns_to_retain=[
        "cluster_id_true",
        "split",
        "adresse_clean",
        "nom_clean",
    ],
)

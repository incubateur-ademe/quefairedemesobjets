-- replace :
-- exposure_stats_nb_acteur_visible_history
-- exposure_stats_nb_acteur_visible_with_siren_history
-- exposure_stats_nb_acteur_visible_with_siret_history
-- exposure_stats_nb_acteur_visible_with_siren_actif_history
-- exposure_stats_nb_acteur_visible_with_siret_actif_history
-- exposure_stats_rate_acteur_visible_with_siren_history
-- exposure_stats_rate_acteur_visible_with_siret_history
-- exposure_stats_rate_acteur_visible_with_siren_actif_history
-- exposure_stats_rate_acteur_visible_with_siret_actif_history

WITH visible AS (
    SELECT
        COUNT(*) AS nb_total -- acteurs visibles
    FROM {{ ref('base_vueacteur_visible') }}
),
siren AS (
    SELECT
        COUNT(*) AS nb_with_siren
    FROM {{ ref('int_acteur_with_siren') }}
),
siren_actif AS (
    SELECT
        COUNT(*) AS nb_with_siren_actif
    FROM {{ ref('marts_acteur_siren_actif') }}
),
siret AS (
    SELECT
        COUNT(*) AS nb_with_siret
    FROM {{ ref('int_acteur_with_siret') }}
),
siret_actif AS (
    SELECT
        COUNT(*) AS nb_with_siret_actif
    FROM {{ ref('marts_acteur_siret_actif') }}
)

SELECT
    CURRENT_DATE AS date_snapshot,
    visible.nb_total,
    siren.nb_with_siren,
    siren_actif.nb_with_siren_actif,
    siren.nb_with_siren - siren_actif.nb_with_siren_actif as nb_with_siren_inactive,
    siret.nb_with_siret,
    siret_actif.nb_with_siret_actif,
    siret.nb_with_siret - siret_actif.nb_with_siret_actif as nb_with_siret_inactive,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND((siren.nb_with_siren::NUMERIC / visible.nb_total) * 100, 2)
    END AS rate_siren,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND((siren_actif.nb_with_siren_actif::NUMERIC / siren.nb_with_siren) * 100, 2)
    END AS rate_siren_actif,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND(((siren.nb_with_siren - siren_actif.nb_with_siren_actif)::NUMERIC / siren.nb_with_siren) * 100, 2)
    END AS rate_siren_inactive,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND((siret.nb_with_siret::NUMERIC / visible.nb_total) * 100, 2)
    END AS rate_siret,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND((siret_actif.nb_with_siret_actif::NUMERIC / siret.nb_with_siret) * 100, 2)
    END AS rate_siret_actif,
    CASE
        WHEN visible.nb_total = 0 THEN 0
        ELSE ROUND(((siret.nb_with_siret - siret_actif.nb_with_siret_actif)::NUMERIC / siret.nb_with_siret) * 100, 2)
    END AS rate_siret_inactive
FROM visible
CROSS JOIN siren
CROSS JOIN siren_actif
CROSS JOIN siret
CROSS JOIN siret_actif

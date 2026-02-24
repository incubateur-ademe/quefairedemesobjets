-- calculer la distance entre base_random_position
-- et l'acteur le plus proche pour chaque action

WITH position_action AS (
    -- Toutes les combinaisons position x action
    SELECT
        rp.longitude,
        rp.latitude,
        ST_SetSRID(ST_MakePoint(rp.longitude, rp.latitude), 4326)::geography AS geog,
        a.id AS action_id
    FROM {{ ref('base_random_position') }} rp
    CROSS JOIN {{ ref('base_action') }} a
),

distance_to_acteurs AS (
    -- Calculer la distance entre chaque position et chaque acteur qui propose l'action
    -- Filtre: uniquement les acteurs à moins de 30 km (ST_DWithin utilise les index spatiaux)
    SELECT
        pa.longitude,
        pa.latitude,
        pa.action_id,
        va.identifiant_unique AS acteur_id,
        va.latitude AS acteur_latitude,
        va.longitude AS acteur_longitude,
        ST_Distance(pa.geog, va.location::geography) AS distance_m
    FROM position_action pa
    INNER JOIN {{ ref('base_vuepropositionservice_visible') }} vps
        ON pa.action_id = vps.action_id
    INNER JOIN {{ ref('base_vueacteur_visible') }} va
        ON vps.acteur_id = va.identifiant_unique
    WHERE ST_DWithin(pa.geog, va.location::geography, 100000)  -- 30 km en mètres
),

ranked AS (
    -- Classer les acteurs par distance pour chaque position/action
    -- et compter le nombre total de solutions dans les 30 km
    SELECT
        longitude,
        latitude,
        action_id,
        acteur_id,
        acteur_latitude,
        acteur_longitude,
        distance_m,
        ROW_NUMBER() OVER (
            PARTITION BY longitude, latitude, action_id
            ORDER BY distance_m
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY longitude, latitude, action_id
        ) AS nb_solutions_100km
    FROM distance_to_acteurs
)

SELECT
    longitude,
    latitude,
    action_id,
    acteur_id,
    acteur_latitude,
    acteur_longitude,
    distance_m,
    nb_solutions_100km
FROM ranked
WHERE rn = 1
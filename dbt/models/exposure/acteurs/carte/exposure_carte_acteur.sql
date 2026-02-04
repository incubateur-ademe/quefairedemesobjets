SELECT *,
    CAST(ST_X(location::geometry) AS DOUBLE PRECISION) AS latitude,
    CAST(ST_Y(location::geometry) AS DOUBLE PRECISION) AS longitude
FROM {{ ref('marts_carte_acteur') }} WHERE lieu_prestation != 'A_DOMICILE' OR lieu_prestation IS NULL
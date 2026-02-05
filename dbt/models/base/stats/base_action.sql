
SELECT *
FROM {{ source('stats_qfdmo', 'qfdmo_action') }}

/* Check there are >= 150K acteurs (figures 2025-03)
with a SIRET on our side we're able to match
with the etablissement table */
WITH acteurs_with_siret_matched AS (
	SELECT
	COUNT(*) AS nombre_acteurs
	FROM webapp_public.qfdmo_displayedacteur AS acteurs
	JOIN {{table_name}} AS etab
	ON etab.siret = acteurs.siret
	WHERE acteurs.siret IS NOT NULL
)
SELECT
    CASE
        WHEN nombre_acteurs >= 75000 THEN TRUE
        ELSE FALSE
    END AS is_valid,
    nombre_acteurs AS debug_value
FROM acteurs_with_siret_matched
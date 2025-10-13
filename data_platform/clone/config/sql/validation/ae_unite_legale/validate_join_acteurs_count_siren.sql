WITH acteurs_with_siren_matched AS (
	SELECT
	COUNT(*) AS nombre_acteurs
	FROM webapp_public.qfdmo_displayedacteur AS acteurs
	JOIN {{table_name}} AS unite
	ON unite.siren = acteurs.siren
	WHERE acteurs.siren IS NOT NULL
)
SELECT
    CASE
        WHEN nombre_acteurs >= 75000 THEN TRUE
        ELSE FALSE
    END AS is_valid,
    nombre_acteurs AS debug_value
FROM acteurs_with_siren_matched
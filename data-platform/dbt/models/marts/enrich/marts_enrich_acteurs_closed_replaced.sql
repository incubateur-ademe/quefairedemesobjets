{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'closed', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

WITH potential_replacements AS (
	SELECT

		-- Candidates acteur data
		candidates.*,

		-- Suggestions
		acteur_type_id AS suggest_acteur_type_id,
		acteur_longitude AS suggest_longitude,
		acteur_latitude AS suggest_latitude,
		suggests.siret AS suggest_siret,
		LEFT(suggests.siret,9) AS suggest_siren,
		LEFT(candidates.acteur_siret,9) = LEFT(suggests.siret,9) AS suggest_siret_is_from_same_siren,
		suggests.nom AS suggest_nom,
		suggests.naf AS suggest_naf,
		suggests.ville AS suggest_ville,
		suggests.code_postal AS suggest_code_postal,
		suggests.adresse AS suggest_adresse,

		-- Matching
		{{ target.schema }}.udf_columns_words_in_common_count(
			candidates.acteur_nom_normalise,
			{{ target.schema }}.udf_normalize_string_for_match(suggests.nom)
		) AS noms_nombre_mots_commun,
		ROW_NUMBER() OVER (
			PARTITION BY candidates.acteur_siret
			ORDER BY
				-- Prioritize suggests from same company
				CASE
					WHEN LEFT(candidates.acteur_siret,9) = LEFT(suggests.siret,9) THEN 1
					ELSE 0
				END DESC,
				-- Then etablissements with more words in common
				{{ target.schema }}.udf_columns_words_in_common_count(
					candidates.acteur_nom_normalise,
					{{ target.schema }}.udf_normalize_string_for_match(suggests.nom)
				) DESC
		) AS replacement_priority
	/*
	JOINS: candidates are our acteurs, suggests are etablissements
	with a matching naf, code_postal, adresse and adresse_numero
	*/
	FROM {{ ref('marts_enrich_acteurs_closed_candidates') }} AS candidates
	INNER JOIN {{ ref('int_ae_etablissement') }} AS suggests
	ON suggests.naf = candidates.etab_naf
	AND suggests.code_postal = candidates.etab_code_postal
	AND suggests.adresse_numero = candidates.etab_adresse_numero
	AND suggests.adresse_normalize_string_for_match = {{ target.schema }}.udf_normalize_string_for_match(candidates.etab_adresse)
	WHERE suggests.est_actif
	-- Fields which must be non-NULL for a replacement to be considered
	AND suggests.code_postal IS NOT NULL
	AND suggests.adresse IS NOT NULL
	/* To reduce false positives with generic addresses
	such as ZA, ZI containing multiple instances of similar
	stores (e.g. supermarkets), we force presence
	of street number, which later will be used
	as condition for matching */
	AND suggests.adresse_numero IS NOT NULL
)
SELECT * FROM potential_replacements
WHERE replacement_priority=1
/* We don't want to propose suggests with unavailable names */
AND suggest_nom != {{ value_unavailable() }}
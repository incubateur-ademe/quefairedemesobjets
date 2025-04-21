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

		-- Replacements
		replacements.siret AS suggest_siret,
		LEFT(candidates.acteur_siret,9) = LEFT(replacements.siret,9) AS suggest_siret_is_from_same_siren,
		replacements.nom AS suggest_nom,
		replacements.naf AS suggest_naf,
		replacements.ville AS suggest_ville,
		replacements.code_postal AS suggest_code_postal,
		replacements.adresse AS suggest_adresse,

		-- Matching
		udf_columns_words_in_common_count(
			candidates.acteur_nom_normalise,
			udf_normalize_string_for_match(replacements.nom)
		) AS noms_nombre_mots_commun,
		ROW_NUMBER() OVER (
			PARTITION BY candidates.acteur_siret
			ORDER BY
				-- Prioritize replacements from same company
				CASE
					WHEN LEFT(candidates.acteur_siret,9) = LEFT(replacements.siret,9) THEN 1
					ELSE 0
				END DESC,
				-- Then etablissements with more words in common
				udf_columns_words_in_common_count(
					candidates.acteur_nom_normalise,
					udf_normalize_string_for_match(replacements.nom)
				) DESC
		) AS replacement_priority
	/*
	JOINS: candidates are our acteurs, replacements are etablissements
	with a matching naf, code_postal, adresse and adresse_numero
	*/
	FROM {{ ref('marts_enrich_acteurs_closed_candidates') }} AS candidates
	INNER JOIN {{ ref('int_ae_etablissement') }} AS replacements
	ON replacements.naf = candidates.etab_naf
	AND replacements.code_postal = candidates.etab_code_postal
	AND replacements.adresse_numero = candidates.etab_adresse_numero
	AND udf_normalize_string_for_match(replacements.adresse) = udf_normalize_string_for_match(candidates.etab_adresse)
	WHERE replacements.est_actif
	-- Fields which must be non-NULL for a replacement to be considered
	AND replacements.code_postal IS NOT NULL
	AND replacements.adresse IS NOT NULL
	/* To reduce false positives with generic addresses
	such as ZA, ZI containing multiple instances of similar
	stores (e.g. supermarkets), we force presence
	of street number, which later will be used
	as condition for matching */
	AND replacements.adresse_numero IS NOT NULL
)
SELECT * FROM potential_replacements
WHERE replacement_priority=1
/* We don't want to propose replacements with unavailable names */
AND suggest_nom != {{ value_unavailable() }}
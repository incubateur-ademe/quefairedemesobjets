{{
  config(
    materialized = 'view',
    tags=['marts', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

WITH potential_replacements AS (
	SELECT
		candidates.acteur_id AS acteur_id,
		candidates.acteur_statut AS acteur_statut,
		candidates.siret AS acteur_siret,
		replacements.siret AS remplacer_siret,
		CASE
			WHEN LEFT(candidates.siret,9) = LEFT(replacements.siret,9) THEN 1
			ELSE 0
		END AS remplacer_meme_siren,
		candidates.acteur_nom,
		replacements.nom AS remplacer_nom,
		columns_words_in_common_count(
			candidates.acteur_nom_normalise,
			udf_normalize_string_alpha_for_match(replacements.nom)
		) AS noms_nombre_mots_commun,
		candidates.acteur_commentaires AS acteur_commentaires,
		replacements.naf AS naf,
		replacements.ville AS ville,
		replacements.code_postal AS code_postal,
		replacements.adresse AS adresse,
		ROW_NUMBER() OVER (
			PARTITION BY candidates.siret
			ORDER BY
				-- Prioritize replacements from same company
				CASE
					WHEN LEFT(candidates.siret,9) = LEFT(replacements.siret,9) THEN 1
					ELSE 0
				END DESC,
				-- Then etablissements with more words in common
				columns_words_in_common_count(
					candidates.acteur_nom_normalise,
					udf_normalize_string_alpha_for_match(replacements.nom)
				) DESC
		) AS replacement_priority
	FROM {{ ref('marts_enrich_ae_closed_candidates') }} AS candidates
	INNER JOIN {{ ref('int_ae_etablissement') }} AS replacements
	ON replacements.naf = candidates.etab_naf
	AND replacements.code_postal = candidates.etab_code_postal
	AND replacements.adresse = candidates.etab_adresse
	WHERE replacements.est_actif
)
SELECT * FROM potential_replacements
WHERE replacement_priority=1
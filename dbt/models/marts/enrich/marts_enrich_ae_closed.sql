/*
Model to find entries from AE's etablissement which are
potential replacements for closed acteurs.

Code is repetitive (e.g. same logic in SELECT and ROW_NUMBER) and
could be made more concise with an intermediary CTE. However from experience,
intermediate CTEs lead to slower performance (we constraint the planner)
than just letting the query planner do its job. Thus for now, I focus
on performance given the 40M rows

Notes:
 - 🧹 Pre-matching/filtering at SQL level to reduce data size (40M rows)
 - 👁️‍🗨️ Keeping as view to always re-evaluate vs. ever changing QFDMO data
*/
{{
  config(
    materialized = 'view',
    tags=['marts', 'ae', 'annuaire_entreprises', 'etablissement', 'closed'],
  )
}}
-- Starting from our acteurs we can match via SIRET
WITH acteurs_with_siret AS (
	SELECT
        LEFT(siret,9) AS siren,
        siret,
        nom AS acteur_nom,
        udf_normalize_string_alpha_for_match(nom) AS acteur_nom_normalise,
        identifiant_unique AS acteur_id,
        commentaires AS acteur_commentaires,
        statut AS statut
	FROM {{ ref('marts_carte_acteur') }}
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
),
/* Filtering on closed establishments
note: there is another
 */
closed AS (
SELECT
	etab.siret,
	etab.est_actif AS etab_est_actif,
	etab.code_postal AS etab_code_postal,
	etab.adresse AS etab_adresse,
  etab.naf AS etab_naf,
	acteurs.acteur_id,
	acteurs.acteur_nom,
	acteurs.acteur_nom_normalise,
	acteurs.acteur_commentaires
FROM acteurs_with_siret AS acteurs
JOIN {{ ref('int_ae_etablissement') }} AS etab ON acteurs.siret = etab.siret
/*
    By NOT filtering on unite_est_actif we have an opportunite to get replacements
    from the same unite (SIREN)
*/
WHERE NOT etab.est_actif
), ae_potential_replacements AS (
	SELECT
		closed.acteur_id AS acteur_id,
		closed.siret AS acteur_siret,
		replacements.siret AS remplacer_siret,
		CASE
			WHEN LEFT(closed.siret,9) = LEFT(replacements.siret,9) THEN 1
			ELSE 0
		END AS remplacer_meme_siren,
		closed.acteur_nom,
		replacements.nom AS remplacer_nom,
		columns_words_in_common_count(
			closed.acteur_nom_normalise,
			udf_normalize_string_alpha_for_match(replacements.nom)
		) AS noms_nombre_mots_commun,
		closed.acteur_commentaires AS acteur_commentaires,
		replacements.naf AS naf,
		replacements.ville AS ville,
		replacements.code_postal AS code_postal,
		replacements.adresse AS adresse,
		ROW_NUMBER() OVER (
			PARTITION BY closed.siret
			ORDER BY
				-- Prioritize replacements from same company
				CASE
					WHEN LEFT(closed.siret,9) = LEFT(replacements.siret,9) THEN 1
					ELSE 0
				END DESC,
				-- Then etablissements with more words in common
				columns_words_in_common_count(
					closed.acteur_nom_normalise,
					udf_normalize_string_alpha_for_match(replacements.nom)
				) DESC
		) AS rn
	FROM closed
	INNER JOIN {{ ref('int_ae_etablissement') }} AS replacements
	ON replacements.naf = closed.etab_naf
	AND replacements.code_postal = closed.etab_code_postal
	AND replacements.adresse = closed.etab_adresse
	WHERE replacements.est_actif
)
SELECT * FROM ae_potential_replacements
WHERE rn=1
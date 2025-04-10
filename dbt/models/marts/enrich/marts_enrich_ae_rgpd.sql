/*
Model to find entries from AE's unite legal which directors names
around found inside our acteurs names.

Notes:
 - 🧹 Pre-matching/filtering at SQL level to reduce data size (13M rows)
 - 👁️‍🗨️ Keeping as view to always re-evaluate vs. ever changing QFDMO data
*/
{{
  config(
    materialized = 'view',
    tags=['marts', 'ae', 'annuaire_entreprises', 'unite_legale', 'rgpd'],
  )
}}

WITH acteurs_with_siren AS (
	SELECT
		LEFT(siret,9) AS siren,
		identifiant_unique AS acteur_id,
		TRIM(REGEXP_REPLACE(
			CONCAT(nom || ', ' || nom_officiel || ', ' || nom_commercial),
			', , ',
			'')
		) AS acteur_noms_origine,
		udf_normalize_string_alpha_for_match(CONCAT(nom || ' ' || nom_officiel || ' ' || nom_commercial)) AS acteur_noms_normalises,
		commentaires AS acteur_commentaires
	FROM {{ ref('marts_carte_acteur') }}
	/*
	We have normalization issues with our SIREN field in our DB
	and we obtain better matching by reconstructing SIREN via SIRET
	 */
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
	AND {{ acteur_status_is_active() }}
)
SELECT
	-- Common fields
	acteurs.siren,

	-- Acteur fields
	acteur_id,
	acteur_noms_origine,
	acteur_noms_normalises,
	acteur_commentaires,

	-- Unite legale fields
	/*
	We don't care which one is which, we aggregate to
	reduce data size and we will perform a more precise
	post-match in Python
	*/
	udf_columns_concat_unique_non_empty(
		dirigeant_nom,
		dirigeant_nom_usage,
		dirigeant_pseudonyme,
		dirigeant_prenom1,
		dirigeant_prenom2,
		dirigeant_prenom3,
		dirigeant_prenom4
	) AS ae_dirigeants_noms_prenoms

FROM {{ ref('int_ae_unite_legale') }} AS unite
LEFT JOIN acteurs_with_siren AS acteurs ON acteurs.siren = unite.siren
WHERE
	acteurs.siren IS NOT NULL -- i.e. we have a match
    AND a_dirigeant_noms_ou_prenoms_non_null -- we have some directors names
	AND ( -- Any of the directors names appear in the acteur names
		position(dirigeant_nom IN acteur_noms_normalises) > 0
		OR position(dirigeant_nom_usage IN acteur_noms_normalises) > 0
		OR position(dirigeant_pseudonyme IN acteur_noms_normalises) > 0
		OR position(dirigeant_prenom1 IN acteur_noms_normalises) > 0
		OR position(dirigeant_prenom2 IN acteur_noms_normalises) > 0
		OR position(dirigeant_prenom3 IN acteur_noms_normalises) > 0
		OR position(dirigeant_prenom4 IN acteur_noms_normalises) > 0
	)
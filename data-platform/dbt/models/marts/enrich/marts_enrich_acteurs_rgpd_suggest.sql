/*
Model to find entries from AE's unite legal which directors names
around found inside our acteurs names.

Notes:
 - 🧹 Pre-matching/filtering at SQL level to reduce data size (13M rows)
*/
{{
  config(
    materialized = 'view',
    tags=['marts', 'enrich', 'ae', 'annuaire_entreprises', 'unite_legale', 'rgpd'],
  )
}}

WITH acteurs_with_siren AS (
	SELECT
		identifiant_unique,
		acteur_type_id,
		source_id,
		-- Extract SIREN from SIRET as we have SIREN issues in our DB
		LEFT(siret,9) AS siren,
		identifiant_unique AS id,
		TRIM(REGEXP_REPLACE(
			CONCAT(nom || ', ' || nom_officiel || ', ' || nom_commercial),
			', , ',
			'')
		) AS noms_origine,
		{{ target.schema }}.udf_normalize_string_for_match(CONCAT(nom || ' ' || nom_officiel || ' ' || nom_commercial)) AS noms_normalises,
		commentaires,
		statut
	FROM {{ source('enrich', 'qfdmo_vueacteur') }} AS acteurs
	/*
	We have normalization issues with our SIREN field in our DB
	and we obtain better matching by reconstructing SIREN via SIRET
	 */
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
), unite_matching_acteurs_on_siren AS (
	SELECT
		acteurs.identifiant_unique AS acteur_id,
		acteurs.acteur_type_id AS acteur_type_id,
		acteurs.source_id AS acteur_source_id,
		acteurs.siren AS acteur_siren,
		acteurs.noms_origine AS acteur_noms_origine,
		acteurs.noms_normalises AS acteur_noms_normalises,
		acteurs.commentaires AS acteur_commentaires,
		acteurs.statut AS acteur_statut,
		-- Unite legale fields
		/*
		We don't care which one is which, we aggregate to
		reduce data size and we will perform a more precise
		post-match in Python
		*/
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_nom) AS unite_dirigeant_nom_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_nom_usage) AS unite_dirigeant_nom_usage_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_pseudonyme) AS unite_dirigeant_pseudonyme_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_prenom1) AS unite_dirigeant_prenom1_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_prenom2) AS unite_dirigeant_prenom2_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_prenom3) AS unite_dirigeant_prenom3_normalise,
		{{ target.schema }}.udf_normalize_string_for_match(dirigeant_prenom4) AS unite_dirigeant_prenom4_normalise,
		{{ target.schema }}.udf_columns_concat_unique_non_empty(
			dirigeant_nom,
			dirigeant_nom_usage,
			dirigeant_pseudonyme,
			dirigeant_prenom1,
			dirigeant_prenom2,
			dirigeant_prenom3,
			dirigeant_prenom4
		) AS unite_dirigeants_noms_prenoms
	FROM {{ ref('int_ae_unite_legale') }} AS unite
	LEFT JOIN acteurs_with_siren AS acteurs ON acteurs.siren = unite.siren
	WHERE
		unite.est_actif IS FALSE -- we only anonymize inactive acteurs
		AND a_dirigeant_noms_ou_prenoms_non_null -- unite with any directors names available
		AND acteurs.siren IS NOT NULL
), suggestions_with_minimum_matching_words AS (
	SELECT
		*
	FROM unite_matching_acteurs_on_siren
	WHERE ( -- Any of the directors names appear in the acteur names
		position(unite_dirigeant_nom_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_nom_usage_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_pseudonyme_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_prenom1_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_prenom2_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_prenom3_normalise IN acteur_noms_normalises) > 0
		OR position(unite_dirigeant_prenom4_normalise IN acteur_noms_normalises) > 0
	)
)
SELECT
	'Anonymisation RGPD' AS suggest_cohort,
	*
FROM suggestions_with_minimum_matching_words
/*
Acteurs which SIRET is closed in AE's etablissement

Notes:
 - 📦 Materialized as table but refreshed by DAG enrich_acteurs_closed
	as many models/tests depending on each other = would take too long
*/
{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'closed', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}
-- Starting from our acteurs we can match via SIRET
WITH acteurs_with_siret AS (
	SELECT
<<<<<<< HEAD
		-- Acteur columns
=======
		-- Common columns
        LEFT(siret,9) AS siren,
        siret,

		-- Acteur columns
        nom AS acteur_nom,
        udf_normalize_string_for_match(nom) AS acteur_nom_normalise,
>>>>>>> 00ec04b2 (DAG & Admin UI fonctionnels)
        identifiant_unique AS acteur_id,
		siret AS acteur_siret,
		LEFT(siret,9) AS acteur_siren,
        nom AS acteur_nom,
        udf_normalize_string_for_match(nom) AS acteur_nom_normalise,
        commentaires AS acteur_commentaires,
        statut AS acteur_statut,
		acteur_type_id,
<<<<<<< HEAD
		source_id AS acteur_source_id,
		adresse AS acteur_adresse,
		code_postal AS acteur_code_postal,
		ville AS acteur_ville,
		location AS acteur_location
=======
		acteur_type_code,
		source_id AS acteur_source_id,
		source_code AS acteur_source_code,
		adresse AS acteur_adresse,
		code_postal AS acteur_code_postal,
		ville AS acteur_ville
>>>>>>> 00ec04b2 (DAG & Admin UI fonctionnels)

	FROM {{ ref('marts_carte_acteur') }}
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
),
/* Filtering on etab closed (NOT etab.est_actif) BUT
not on unite closed (NOT unite_est_actif) because
open unite might bring potential replacements */
etab_closed_candidates AS (
SELECT
	-- acteurs
	acteurs.acteur_id,
	acteurs.acteur_siret,
	acteurs.acteur_siren,
	acteurs.acteur_type_id,
	acteurs.acteur_source_id,
	acteurs.acteur_statut,
	acteurs.acteur_nom,
	acteurs.acteur_nom_normalise,
	acteurs.acteur_commentaires,
	acteurs.acteur_adresse,
	acteurs.acteur_code_postal,
	acteurs.acteur_ville,
	CASE WHEN acteurs.acteur_location IS NULL THEN NULL ELSE ST_X(acteurs.acteur_location) END AS acteur_longitude,
	CASE WHEN acteurs.acteur_location IS NULL THEN NULL ELSE ST_Y(acteurs.acteur_location) END AS acteur_latitude,

	-- etablissement
	etab.unite_est_actif AS unite_est_actif,
	etab.est_actif AS etab_est_actif,
	etab.code_postal AS etab_code_postal,
	etab.adresse_numero AS etab_adresse_numero,
	etab.adresse AS etab_adresse,
	etab.adresse_complement AS etab_adresse_complement,
  	etab.naf AS etab_naf

FROM acteurs_with_siret AS acteurs
JOIN {{ ref('int_ae_etablissement') }} AS etab ON acteurs.acteur_siret = etab.siret
WHERE etab.est_actif IS FALSE
/* To reduce false positives with generic addresses
such as ZA, ZI containing multiple instances of similar
stores (e.g. supermarkets), we force presence
of street number, which later will be used
as condition for matching */
AND etab.adresse_numero IS NOT NULL
)

SELECT * FROM etab_closed_candidates
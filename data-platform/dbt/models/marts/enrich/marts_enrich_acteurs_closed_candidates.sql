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
		-- Acteur columns
        identifiant_unique AS acteur_id,
		identifiant_externe AS acteur_id_externe,
		siret AS acteur_siret,
		LEFT(siret,9) AS acteur_siren,
        nom AS acteur_nom,
        {{ target.schema }}.udf_normalize_string_for_match(nom) AS acteur_nom_normalise,
        commentaires AS acteur_commentaires,
        statut AS acteur_statut,
		acteur_type_id,
		source_id AS acteur_source_id,
		adresse AS acteur_adresse,
		code_postal AS acteur_code_postal,
		ville AS acteur_ville,
		location AS acteur_location

	FROM {{ source('enrich', 'qfdmo_vueacteur') }} AS acteurs
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
	AND statut = 'ACTIF'
	AND (est_dans_carte IS TRUE OR est_dans_opendata IS TRUE)
),
/* Filtering on etab closed (NOT etab.est_actif) BUT
not on unite closed (NOT unite_est_actif) because
open unite might bring potential replacements */
etab_closed_candidates AS (
SELECT
	-- acteurs
	acteurs.acteur_id,
	acteurs.acteur_id_externe,
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
)

SELECT * FROM etab_closed_candidates
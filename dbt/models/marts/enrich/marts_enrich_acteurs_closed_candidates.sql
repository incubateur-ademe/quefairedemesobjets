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
        LEFT(siret,9) AS siren,
        siret,
        nom AS acteur_nom,
        udf_normalize_string_alpha_for_match(nom) AS acteur_nom_normalise,
        identifiant_unique AS acteur_id,
        commentaires AS acteur_commentaires,
        statut AS acteur_statut,
		acteur_type_id
	FROM {{ ref('marts_carte_acteur') }}
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
),
/* Filtering on etab closed (NOT etab.est_actif) BUT
not on unite closed (NOT unite_est_actif) because
open unite might bring potential replacements */
etab_closed_candidates AS (
SELECT
	etab.siret,
	etab.unite_est_actif AS unite_est_actif,
	etab.est_actif AS etab_est_actif,
	etab.code_postal AS etab_code_postal,
	etab.adresse AS etab_adresse,
  	etab.naf AS etab_naf,
	acteurs.acteur_id,
	acteurs.acteur_statut,
	acteurs.acteur_nom,
	acteurs.acteur_nom_normalise,
	acteurs.acteur_commentaires,
	acteurs.acteur_type_id
FROM acteurs_with_siret AS acteurs
JOIN {{ ref('int_ae_etablissement') }} AS etab ON acteurs.siret = etab.siret
WHERE etab.est_actif IS FALSE
)
SELECT * FROM etab_closed_candidates
/*
Model to find entries from AE's etablissement which are
potential replacements for etab_closed acteurs.

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
    tags=['marts', 'ae', 'annuaire_entreprises', 'etablissement'],
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
		acteur_type AS acteur_type
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
	acteurs.acteur_type
FROM acteurs_with_siret AS acteurs
JOIN {{ ref('int_ae_etablissement') }} AS etab ON acteurs.siret = etab.siret
WHERE etab.est_actif = FALSE
)
SELECT * FROM etab_closed_candidates
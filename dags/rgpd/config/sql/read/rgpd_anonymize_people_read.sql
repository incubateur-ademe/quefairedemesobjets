WITH acteurs_with_siren AS (
	SELECT
	TRIM(CONCAT(nom || ' ' || nom_officiel || ' ' || nom_commercial)) AS noms,
	LEFT(siret,9) AS siren,
	identifiant_unique,
	commentaires
	FROM qfdmo_displayedacteur
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
	AND commentaires LIKE '%{{filter_comments_contain}}%'
)
SELECT
	unite.siren,
	acteurs.noms AS qfdmo_acteur_noms_origine,
	acteurs.noms AS qfdmo_acteur_noms_comparaison,
	acteurs.identifiant_unique AS qfdmo_acteur_id,
	acteurs.commentaires AS qfdmo_acteur_commentaires,
	unite."prenom1UniteLegale" AS "ae_prenom1UniteLegale",
	unite."prenom2UniteLegale" AS "ae_prenom2UniteLegale",
	unite."prenom3UniteLegale" AS "ae_prenom3UniteLegale",
	unite."prenom4UniteLegale" AS "ae_prenom4UniteLegale",
	unite."nomUniteLegale" AS "ae_nomUniteLegale",
	unite."nomUsageUniteLegale" AS "ae_nomUsageUniteLegale"
FROM clone_ae_unite_legale_in_use AS unite
JOIN acteurs_with_siren AS acteurs ON acteurs.siren = unite.siren
WHERE(
    ("prenom1UniteLegale" IS NOT NULL AND "prenom1UniteLegale" != '[ND]')
	OR ("prenom2UniteLegale" IS NOT NULL AND "prenom2UniteLegale" != '[ND]')
	OR ("prenom3UniteLegale" IS NOT NULL AND "prenom3UniteLegale" != '[ND]')
	OR ("prenom4UniteLegale" IS NOT NULL AND "prenom4UniteLegale" != '[ND]')
	OR ("nomUniteLegale" IS NOT NULL AND "nomUniteLegale" != '[ND]')
	OR ("nomUsageUniteLegale" IS NOT NULL AND "nomUsageUniteLegale" != '[ND]')
)
WITH acteurs_with_siret AS (
	SELECT
	TRIM(CONCAT(nom || ' ' || nom_officiel || ' ' || nom_commercial)) AS noms,
	LEFT(siret,9) AS siren,
	siret,
	identifiant_unique,
	commentaires
	FROM qfdmo_displayedacteur
	WHERE siret IS NOT NULL AND siret != '' AND LENGTH(siret) = 14
)
SELECT
	unite."etatAdministratifUniteLegale" AS "ae_etatAdministratifUniteLegale",
	etab."etatAdministratifEtablissement" AS "ae_etatAdministratifEtablissement",
	unite.siren,
	etab.siret,
	acteurs.identifiant_unique AS qfdmo_acteur_id,
	acteurs.noms AS qfdmo_acteur_noms,
	acteurs.commentaires AS qfdmo_acteur_commentairese
FROM acteurs_with_siret AS acteurs
JOIN clone_ae_unite_legale_in_use AS unite ON acteurs.siren = unite.siren
JOIN clone_ae_etablissement_in_use AS etab ON acteurs.siret = etab.siret
WHERE
    -- https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/templates/api/documentation/download.jag?tenant=carbon.super&resourceUrl=/registry/resource/_system/governance/apimgt/applicationdata/provider/insee/Sirene/V3/documentation/files/INSEE%20Documentation%20API%20Sirene%20Variables.pdf
	-- 'C' pour "Cessée"
	unite."etatAdministratifUniteLegale" = 'C'
	OR
	-- 'F' pour "Fermé"
	etab."etatAdministratifEtablissement" = 'F'
with actions_by_actor as (
select
	acteur_id,
	(1 = any(array_agg(action_id))) as action_reparer,
	(2 = any(array_agg(action_id))) as action_acheter,
	(3 = any(array_agg(action_id))) as action_revendre,
	(4 = any(array_agg(action_id))) as action_donner,
	(5 = any(array_agg(action_id))) as action_louer,
	(6 = any(array_agg(action_id))) as action_mettreenlocation,
	(7 = any(array_agg(action_id))) as action_emprunter,
	(8 = any(array_agg(action_id))) as action_preter,
	(9 = any(array_agg(action_id))) as action_echanger,
	(11 = any(array_agg(action_id))) as action_trier,
	(12 = any(array_agg(action_id))) as action_rapporter
from
	qfdmo_vuepropositionservice
group by
	acteur_id
),
-- Sélection des variables à la maille acteur avec les actions précédemment sélectionnées
features as (
select
	identifiant_unique,
	nom,
	description,
	acteur_type_id,
	adresse,
	adresse_complement,
	code_postal,
	ville,
	url,
	email,
	"location",
	telephone,
	nom_commercial,
	nom_officiel,
	siren,
	siret,
	source_id,
	naf_principal,
	horaires_osm,
	horaires_description,
	public_accueilli,
	reprise,
	exclusivite_de_reprisereparation,
	uniquement_sur_rdv,
	consignes_dacces,
	action_principale_id,
	lieu_prestation,
	latitude,
	longitude,
	code_commune_insee,
	epci_id,
	aba.*
from
	qfdmo_vueacteur qv
left join actions_by_actor aba on
	qv.identifiant_unique = aba.acteur_id)
-- Join avec les acteurs sélectionnés dans le dataset
select
	dt.*,
	f.nom as nom,
	f.description as description,
	f.acteur_type_id as acteur_type_id,
	f.adresse as adresse,
	f.adresse_complement as adresse_complement,
	f.code_postal as code_postal,
	f.ville as ville,
	f.url as url,
	f.email as email,
	f.telephone as telephone,
	f.nom_commercial as nom_commercial,
	f.nom_officiel as nom_officiel,
	f.siren as siren,
	f.siret as siret,
	f.source_id as source_id,
	f.naf_principal as naf_principal,
	f.horaires_osm as horaires_osm,
	f.horaires_description as horaires_description,
	f.public_accueilli as public_accueilli,
	f.reprise as reprise,
	f.exclusivite_de_reprisereparation as exclusivite_de_reprisereparation,
	f.uniquement_sur_rdv as uniquement_sur_rdv,
	f.consignes_dacces as consignes_dacces,
	f.action_principale_id as action_principale_id,
	f.lieu_prestation as lieu_prestation,
	f.latitude as latitude,
	f.longitude as longitude,
	f.code_commune_insee as code_commune_insee,
	f.epci_id as epci_id,
	f.action_reparer as action_reparer,
	f.action_acheter as action_acheter,
	f.action_revendre as action_revendre,
	f.action_donner as action_donner,
	f.action_louer as action_louer,
	f.action_mettreenlocation as action_mettreenlocation,
	f.action_emprunter as action_emprunter,
	f.action_preter as action_preter,
	f.action_echanger as action_echanger,
	f.action_trier as action_trier,
	f.action_rapporter as action_rapporter
from
	luis._ml_dataset_tmp dt
left join features f on
	dt.identifiant_unique = f.identifiant_unique

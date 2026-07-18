with actions_by_actor as (
-- D'abord on calcule les actions des parents sur la base de leurs enfants
select
	qv.identifiant_unique as acteur_id,
	(1 = any(array_agg(qv2.action_id))) as action_reparer,
	(2 = any(array_agg(qv2.action_id))) as action_acheter,
	(3 = any(array_agg(qv2.action_id))) as action_revendre,
	(4 = any(array_agg(qv2.action_id))) as action_donner,
	(5 = any(array_agg(qv2.action_id))) as action_louer,
	(6 = any(array_agg(qv2.action_id))) as action_mettreenlocation,
	(7 = any(array_agg(qv2.action_id))) as action_emprunter,
	(8 = any(array_agg(qv2.action_id))) as action_preter,
	(9 = any(array_agg(qv2.action_id))) as action_echanger,
	(11 = any(array_agg(qv2.action_id))) as action_trier,
	(12 = any(array_agg(qv2.action_id))) as action_rapporter
from
	qfdmo_vueacteur qv
inner join qfdmo_vueacteur qv3 on
	qv.est_parent
	and qv.identifiant_unique = qv3.parent_id
	and qv3.statut <> 'SUPPRIME'
inner join qfdmo_vuepropositionservice qv2 on
	qv3.identifiant_unique = qv2.acteur_id
group by
	1
union all -- on joint les actions des enfants
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
	f.nom as nom_i,
	f.description as description_i,
	f.acteur_type_id as acteur_type_id_i,
	f.adresse as adresse_i,
	f.adresse_complement as adresse_complement_i,
	f.code_postal as code_postal_i,
	f.ville as ville_i,
	f.url as url_i,
	f.email as email_i,
	f.telephone as telephone_i,
	f.nom_commercial as nom_commercial_i,
	f.nom_officiel as nom_officiel_i,
	f.siren as siren_i,
	f.siret as siret_i,
	f.source_id as source_id_i,
	f.naf_principal as naf_principal_i,
	f.horaires_osm as horaires_osm_i,
	f.horaires_description as horaires_description_i,
	f.public_accueilli as public_accueilli_i,
	f.reprise as reprise_i,
	f.exclusivite_de_reprisereparation as exclusivite_de_reprisereparation_i,
	f.uniquement_sur_rdv as uniquement_sur_rdv_i,
	f.consignes_dacces as consignes_dacces_i,
	f.action_principale_id as action_principale_id_i,
	f.lieu_prestation as lieu_prestation_i,
	f.latitude as latitude_i,
	f.longitude as longitude_i,
	f.code_commune_insee as code_commune_insee_i,
	f.epci_id as epci_id_i,
	f.action_reparer as action_reparer_i,
	f.action_acheter as action_acheter_i,
	f.action_revendre as action_revendre_i,
	f.action_donner as action_donner_i,
	f.action_louer as action_louer_i,
	f.action_mettreenlocation as action_mettreenlocation_i,
	f.action_emprunter as action_emprunter_i,
	f.action_preter as action_preter_i,
	f.action_echanger as action_echanger_i,
	f.action_trier as action_trier_i,
	f.action_rapporter as action_rapporter_i,
	f2.nom as nom_j,
	f2.description as description_j,
	f2.acteur_type_id as acteur_type_id_j,
	f2.adresse as adresse_j,
	f2.adresse_complement as adresse_complement_j,
	f2.code_postal as code_postal_j,
	f2.ville as ville_j,
	f2.url as url_j,
	f2.email as email_j,
	f2.telephone as telephone_j,
	f2.nom_commercial as nom_commercial_j,
	f2.nom_officiel as nom_officiel_j,
	f2.siren as siren_j,
	f2.siret as siret_j,
	f2.source_id as source_id_j,
	f2.naf_principal as naf_principal_j,
	f2.horaires_osm as horaires_osm_j,
	f2.horaires_description as horaires_description_j,
	f2.public_accueilli as public_accueilli_j,
	f2.reprise as reprise_j,
	f2.exclusivite_de_reprisereparation as exclusivite_de_reprisereparation_j,
	f2.uniquement_sur_rdv as uniquement_sur_rdv_j,
	f2.consignes_dacces as consignes_dacces_j,
	f2.action_principale_id as action_principale_id_j,
	f2.lieu_prestation as lieu_prestation_j,
	f2.latitude as latitude_j,
	f2.longitude as longitude_j,
	f2.code_commune_insee as code_commune_insee_j,
	f2.epci_id as epci_id_j,
	f2.action_reparer as action_reparer_j,
	f2.action_acheter as action_acheter_j,
	f2.action_revendre as action_revendre_j,
	f2.action_donner as action_donner_j,
	f2.action_louer as action_louer_j,
	f2.action_mettreenlocation as action_mettreenlocation_j,
	f2.action_emprunter as action_emprunter_j,
	f2.action_preter as action_preter_j,
	f2.action_echanger as action_echanger_j,
	f2.action_trier as action_trier_j,
	f2.action_rapporter as action_rapporter_j
from
	luis._ml_dataset_tmp dt
left join features f on
	dt.identifiant_unique_i = f.identifiant_unique
left join features f2 on
	dt.identifiant_unique_j = f2.identifiant_unique

with other_entities_with_cluster as (
select
	qv.identifiant_unique,
	qv.parent_id as cluster_id
from
	qfdmo_vueacteur qv
where
	qv.acteur_type_id != 10
	and qv.statut = 'ACTIF'
	and qv.parent_id is not null
	and qv.identifiant_unique not in (
	select
		identifiant_unique
	from
		{}
		where cluster_id is not null)
	and not qv.est_parent
),
singletons_entities_clusters as ( -- Rattrapage des annotations manuelles négatives qui ont leur propre clusters
select
	qv2.identifiant_unique,
	max(qv2.parent_id) as cluster_id,
	true as was_singleton,
	max(et.identifiant_unique) as initial_entity_id
from {} et
inner join qfdmo_vueacteur qv on et.identifiant_unique = qv.identifiant_unique
inner join qfdmo_vueacteur qv2 on qv.parent_id = qv2.parent_id
where et.cluster_id is null
and qv2.acteur_type_id != 10
and qv2.statut = 'ACTIF'
and not qv2.est_parent
group by 1
)
select
	identifiant_unique,
	cluster_id,
	false as was_singleton,
	null as initial_entity_id
from
	other_entities_with_cluster
union all
select
	identifiant_unique,
	cluster_id,
	was_singleton,
	initial_entity_id
from
	singletons_entities_clusters

drop table if exists luis._entities_with_location_tmp;
create table luis._entities_with_location_tmp as (
select
    et.*,
    qv."location",
    lower(qv.nom) as nom
from
    {} et
left join qfdmo_vueacteur qv on
    et.identifiant_unique = qv.identifiant_unique
);

create index IF NOT EXISTS _entities_with_location_tmp_location_idx on
                luis._entities_with_location_tmp
            using gist (location);

drop table if exists luis._selected_acteurs_tmp;
create table luis._selected_acteurs_tmp as (
with entities_query as (
select
	et.*,
	qv."location"
from
	{} et
left join qfdmo_vueacteur qv on
	et.identifiant_unique = qv.identifiant_unique
),
selected_acteurs as
(
select
	identifiant_unique,
	qv."location",
	lower(qv.nom) as nom
from
	qfdmo_vueacteur qv
where
	qv.acteur_type_id != 10
	and qv.statut = 'ACTIF'
	and qv.parent_id is null
	and qv.identifiant_unique not in (
	select
		identifiant_unique
	from
		entities_query)
	and not qv.est_parent
)
select * from selected_acteurs order by random()
);

create index IF NOT EXISTS _selected_acteurs_tmp_location_idx on
luis._selected_acteurs_tmp
    using gist (location);
select
	sa.identifiant_unique,
	null as cluster_id,
	bool_or(eq.identifiant_unique is not null) as is_100m_close_to_clustered_entity,
	array_agg(distinct eq.identifiant_unique ) FILTER (WHERE eq.identifiant_unique IS NOT NULL) as close_entities,
	array_agg(distinct eq.nom) FILTER (WHERE eq.nom IS NOT NULL) as close_entities_noms,
	sa.nom as nom
from
	luis._selected_acteurs_tmp sa
left join luis._entities_with_location_tmp eq on
	ST_DWITHIN(eq."location", sa."location",100)
group by
	1, sa.nom

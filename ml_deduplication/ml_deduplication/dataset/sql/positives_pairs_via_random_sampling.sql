with pool as
(
select
	qv.identifiant_unique,
	qv.parent_id,
    qv.acteur_type_id,
    qv.source_id
from
	qfdmo_vueacteur qv),
paires_dupliquees as (
select
	least(p.identifiant_unique, p2.identifiant_unique) as identifiant_unique_i,
	greatest(p.identifiant_unique, p2.identifiant_unique) as identifiant_unique_j,
    p.parent_id
from
	pool p
inner join pool p2 on
	p.parent_id = p2.parent_id
	and p.identifiant_unique != p2.identifiant_unique
where
  coalesce(p.source_id, -1) != coalesce(p2.source_id, -2) -- les deux acteurs n'ont pas la même source
  AND coalesce(p.acteur_type_id, -1) != coalesce(p2.acteur_type_id, -2) -- les deux acteurs ne sont pas du même type
  AND p.acteur_type_id!=10 AND p2.acteur_type_id!=10 -- Exclusion des PAV publics
)
select
	identifiant_unique_i,
	identifiant_unique_j,
    parent_id as cluster_id
from
	(
	select
		*,
		row_number() over (partition by identifiant_unique_i,
		identifiant_unique_j) as rn
	from
		paires_dupliquees
)
where
	rn = 1
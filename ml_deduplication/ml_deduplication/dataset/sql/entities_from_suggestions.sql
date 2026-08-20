with suggestions as
(
select
	fpst.*,
	ds.suggestion->'changes'->0->'model_params'->>'id' as id_parent,
	jsonb_path_query_array(ds.contexte, '$.fuzzy_details[*].identifiant_unique') as identifiant_unique_list
from
	{} fpst
inner join data_suggestion ds on
	fpst.suggestion_id = ds.id
),
-- Une ligne par suggestion_id, acteur_id concerné
suggestions_explosees as (
select
	s.suggestion_id,
	string_to_array(true_candidate_filter, ',') as true_candidate_filter,
	id_parent,
	s_lid.id_acteur
from
	suggestions s,
	 jsonb_array_elements_text(s.identifiant_unique_list) as s_lid(id_acteur)
),
-- On filtre les acteurs qui font vraiment partie du cluster
suggestions_filtrees as (
select
	id_acteur as identifiant_unique,
	id_parent as parent_id,
	null as cluster_id
from
	suggestions_explosees
where
	(true_candidate_filter is null)
	or not (id_acteur = any(true_candidate_filter) )
),
-- On va chercher les enfants relatifs aux vrais clusters
enfants as (
select
	identifiant_unique,
	parent_id,
	parent_id as cluster_id
from qfdmo_vueacteur qv
where qv.statut = 'ACTIF'
and (qv.parent_id in (select distinct parent_id from suggestions_filtrees where parent_id is not null))
)
select
	identifiant_unique,
	parent_id,
	cluster_id
from suggestions_filtrees
union all
select
	identifiant_unique,
	parent_id,
	cluster_id
from enfants
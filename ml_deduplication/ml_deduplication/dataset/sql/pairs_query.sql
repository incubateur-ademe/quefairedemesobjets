-- Sélection des suggestions annotées
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
	id_parent,
	s_lid.id_acteur
from
	suggestions s,
	 jsonb_array_elements_text(s.identifiant_unique_list) as s_lid(id_acteur)
),
-- Création des paires
paires_dupliquees as (
select
	s1.suggestion_id,
	least(s1.id_acteur , s2.id_acteur ) as identifiant_unique_i,
	greatest(s1.id_acteur , s2.id_acteur) as identifiant_unique_j,
	coalesce(s1.id_parent,s2.id_parent) as cluster_id,
	row_number() over (partition by least(s1.id_acteur , s2.id_acteur ),
	greatest(s1.id_acteur , s2.id_acteur)) as rn
from
	suggestions_explosees s1
inner join suggestions_explosees s2 on
	s1.suggestion_id = s2.suggestion_id
),
-- Déduplication
paires_dedupliquees as (
select
	pd.suggestion_id,
	identifiant_unique_i,
	identifiant_unique_j,
	cluster_id
from
	paires_dupliquees pd
where
	rn = 1
	and identifiant_unique_i <> identifiant_unique_j
),
-- Ajout des potentiels autres enfants liés au parent suggéré par le clustering (pour créer encore plus de paires négatives)
paires_enfants as (
select
	pd.suggestion_id,
	case
		when qv.identifiant_unique is null then pd.identifiant_unique_i
		else qv.identifiant_unique
	end as identifiant_unique_i,
	case
		when qv2.identifiant_unique is null then pd.identifiant_unique_j
		else qv2.identifiant_unique
	end as identifiant_unique_j,
	cluster_id
from
	paires_dedupliquees pd
left join qfdmo_vueacteur qv on
	pd.identifiant_unique_i = qv.parent_id
left join qfdmo_vueacteur qv2 on
	pd.identifiant_unique_j = qv2.parent_id
where
	identifiant_unique_i <> identifiant_unique_j
),
paires_enfant_dupliques as (
select
	pe.suggestion_id ,
	least(pe.identifiant_unique_i, pe.identifiant_unique_j ) as identifiant_unique_i,
	greatest(pe.identifiant_unique_i, pe.identifiant_unique_j ) as identifiant_unique_j,
	cluster_id
from
	paires_enfants pe
)
select
	identifiant_unique_i,
	identifiant_unique_j,
	cluster_id
from
	(
	select
		*,
		row_number() over (partition by identifiant_unique_i,
		identifiant_unique_j) as rn
	from
		paires_enfant_dupliques
	where identifiant_unique_i<>identifiant_unique_j
)
where
	rn = 1

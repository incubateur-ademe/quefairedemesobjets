with suggestions_avec_creation_de_parent as
(
select
	ds.id,
	ds.statut,
	jsonb_path_query_array(ds.contexte, '$.fuzzy_details[*].identifiant_unique') as identifiant_unique_list,
	ds.suggestion->'changes'->0->'model_params'->>'id' as id_parent,
	ds.suggestion->'changes'->0->>'reason' as suggestion_reason,
	ds.modifie_le
from
	data_suggestion ds
inner join data_suggestioncohorte ds2
on
	ds.suggestion_cohorte_id = ds2.id
	and ds2.type_action = 'CLUSTERING'
where
	ds.contexte->'fuzzy_details' is not null
	and ds.suggestion->'changes'->0->>'reason' in ('1️⃣ 1 seul parent existant → à garder','➕ Pas de parent → à créer')
	and ds.statut='SUCCES'
),
suggestions_explosees as (
select
	s.id,
	s.id_parent,
	s.suggestion_reason,
	s.modifie_le,
	s_lid.id_acteur
from
	suggestions_avec_creation_de_parent s,
	 jsonb_array_elements_text(s.identifiant_unique_list) as s_lid(id_acteur)
where id_acteur::text<>s.id_parent
),
suggestions_avec_parent_existant as (
SELECT
	se.*
from suggestions_explosees se
inner join qfdmo_vueacteur qv on se.id_parent=qv.identifiant_unique
),
suggestions_vrais_negatifs as (
select
	 qv.identifiant_unique,
	 qv."uuid",
	 se.id_parent as suggestion_parent_id,
	 se.id as suggestion_id,
	 se.suggestion_reason
from
	qfdmo_vueacteur qv
inner join suggestions_avec_parent_existant se on qv.identifiant_unique = se.id_acteur and qv.parent_id!=se.id_parent
where
	not qv.est_parent
	and qv.statut <> 'SUPPRIME'
	and qv.modifie_le <= now() - interval '1 day'
)
select
	svn.identifiant_unique as identifiant_unique_i,
	qv.identifiant_unique as identifiant_unique_j
from suggestions_vrais_negatifs svn
inner join 	qfdmo_vueacteur qv
on svn.suggestion_parent_id=qv.parent_id and svn.identifiant_unique!=qv.identifiant_unique
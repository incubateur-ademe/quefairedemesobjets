-- Table temporaire des acteurs clusterisés (parent_id non null) qui servira à la
-- recherche de paires proches de clusters DIFFERENTS.
--
-- On matérialise ces acteurs dans une table temporaire et on ajoute un index
-- GiST sur "location" : contrairement à une requête directe sur la vue
-- qfdmo_vueacteur (qui ne garantit pas l'usage d'un index spatial), cela permet
-- au planificateur d'utiliser un vrai index GiST pour le st_dwithin, ce qui
-- accélère fortement la jointure spatiale sur ~400k lignes.
drop table if exists luis._nearby_clusters_tmp;
create table luis._nearby_clusters_tmp as (
    select
        qv.identifiant_unique,
        qv.parent_id as cluster_id,
        qv."location",
        coalesce(qv.source_id, -1) as source_id
    from
        qfdmo_vueacteur qv
    where
        qv.statut = 'ACTIF'
        and not qv.est_parent
        and qv.parent_id is not null
        and qv.acteur_type_id != 10
);

create index if not exists _nearby_clusters_tmp_location_idx on
    luis._nearby_clusters_tmp
    using gist (location);

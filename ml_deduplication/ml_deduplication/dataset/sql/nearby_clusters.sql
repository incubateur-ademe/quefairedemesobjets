-- Entités appartenant à des clusters (parent_id) DIFFERENTS mais géographiquement
-- proches (<= {nearby_distance_meters} m). C'est le cas typique des centres
-- commerciaux : plusieurs magasins distincts situés au même endroit.
--
-- Ces entités ont toutes un parent_id (cluster connu) : on est donc certain
-- qu'elles sont des entités distinctes -> aucun risque de bruit / faux négatif.
--
-- PERFORMANCE : la table temporaire luis._nearby_clusters_tmp (créée par
-- create_nearby_clusters_tmp_tables.sql) porte un index GiST sur "location".
-- On borne la table "pilote" à un échantillon aléatoire de {sample_size} lignes ;
-- chaque ligne ne regarde que ses voisins proches via l'index GiST, au lieu de
-- balayer toute la table. On n'en garde que les paires de clusters distincts,
-- puis on renvoie TOUTES les entités de ces clusters (clusters complets) afin
-- que l'appelant puisse ajouter des clusters entiers et non des entités isolées.
with echantillon as (
    select
        identifiant_unique,
        cluster_id,
        "location",
        source_id
    from
        luis._nearby_clusters_tmp
    order by
        random()
    limit
        {sample_size}
),
paires_clusters_proches as (
    select distinct
        a.cluster_id as cluster_id_i,
        b.cluster_id as cluster_id_j
    from
        echantillon a
        join luis._nearby_clusters_tmp b
            on a.identifiant_unique < b.identifiant_unique
            and a.cluster_id != b.cluster_id
            and st_dwithin(a."location", b."location", {nearby_distance_meters})
            and a.source_id != b.source_id
),
clusters_proches as (
    select
        cluster_id_i as cluster_id
    from
        paires_clusters_proches
    union
    select
        cluster_id_j as cluster_id
    from
        paires_clusters_proches
)
-- On retourne TOUTES les entités des clusters impliqués dans un voisinage proche
-- de clusters distincts, afin de toujours manipuler des clusters complets.
select
    nc.identifiant_unique,
    nc.cluster_id
from
    luis._nearby_clusters_tmp nc
join clusters_proches cp on
    nc.cluster_id = cp.cluster_id

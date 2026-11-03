"""
Patch de performance pour dedupe.clustering.connected_components.

Diagnostic
----------
`dedupe.clustering.connected_components` (appelée par `dedupe.clustering.cluster`,
donc par `Dedupe.cluster()` / `.partition()`) a DEUX défauts pour un gros volume
de paires (ex: 200k entités / 30M paires) :

1. Elle crée systématiquement un fichier temporaire memmap sur disque pour
   ajouter une colonne "label" à l'edgelist, même si l'edgelist tient
   largement en RAM. Si les IDs de vos records sont des chaînes (ex: UUID
   ou identifiants métier longs), chaque paire stocke 2x cette chaîne en
   largeur fixe numpy (4 octets/caractère en UTF-32) -> c'est ce qui explique
   un fichier de plusieurs dizaines de Go pour "seulement" 30M paires.

2. Son union-find (`dedupe.clustering.union_find`) est une boucle Python pure,
   ET fait un `numpy.unique()` supplémentaire à CHAQUE fusion de deux
   composantes. Sur un graphe dense (30M arêtes / 200k noeuds = degré moyen
   ~300), ça dégrade la complexité au-delà du O(E) attendu d'un vrai
   union-find, en plus du surcoût de l'interpréteur Python.

Solution
--------
On remplace ces deux fonctions par des équivalents qui :
- ne touchent jamais le disque (tout reste en RAM, ce qui est confortable
  pour 30M arêtes une fois qu'on ne duplique plus les IDs string : cf. plus bas)
- utilisent `scipy.sparse.csgraph.connected_components`, un algorithme
  compilé (BFS/DFS, O(V+E) réel) — scipy est déjà une dépendance dure de
  dedupe (utilisée dans ce même fichier pour `scipy.cluster.hierarchy`),
  donc AUCUNE nouvelle dépendance n'est nécessaire. graph_tool n'apporte
  rien ici : à cette échelle (200k noeuds), scipy est déjà quasi optimal
  pour un simple calcul de composantes connexes, et son coût d'installation
  (Boost, Cairo, binaires lourds) n'est pas justifié pour ce seul usage.

Garantie d'identité du résultat
--------------------------------
La décomposition d'un graphe en composantes connexes est mathématiquement
unique : peu importe l'algorithme utilisé, on obtient exactement le même
partitionnement des paires. Le clustering hiérarchique qui a lieu ENSUITE
dans `dedupe.clustering.cluster()` (linkage centroid + fcluster) ne dépend
que de ce partitionnement et de `numpy.unique(sub_graph["pairs"])` (donc de
l'ordre trié des IDs, pas de l'ordre des lignes) — le résultat final
(clusters + scores de confiance) est donc invariant par rapport à
l'implémentation de connected_components.

Le seul endroit sensible à l'ordre est le repli "composante trop grosse"
(`needs_filtering` dans `_connected_components`), qui suppose l'edgelist
triée par score croissant au sein de chaque composante — on reproduit
exactement ce tri (`order=("label", "score")`), donc ce cas reste
identique aussi.

Usage
-----
    import dedupe
    from fast_clustering import patch_dedupe_clustering

    patch_dedupe_clustering()  # une seule fois, avant tout .partition()/.cluster()

    ... reste de votre code inchangé ...
"""

import logging
import time
from collections import defaultdict
from collections.abc import Generator

import numpy
import scipy
import scipy.sparse as sp
from dedupe._typing import Clusters, Scores
from dedupe.clustering import condensedDistance, confidences
from scipy.sparse.csgraph import connected_components as _scipy_connected_components
from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

logger = logging.getLogger(__name__)


def cluster(
    dupes: Scores, threshold: float = 0.5, max_components: int = 30000
) -> Clusters:
    """
    Takes in a list of duplicate pairs and clusters them in to a
    list records that all refer to the same entity based on a given
    threshold

    Keyword arguments:
    threshold -- number between 0 and 1 (default is .5). lowering the
                 number will increase precision, raising it will increase
                 recall
    """
    distance_threshold = 1 - threshold
    dupe_sub_graphs = connected_components(dupes, max_components)

    with tqdm_logging_redirect():
        for sub_graph in tqdm(
            dupe_sub_graphs, desc="Processing sub-graphs", leave=False
        ):
            if len(sub_graph) > 1:
                i_to_id, condensed_distances, N = condensedDistance(sub_graph)

                linkage = scipy.cluster.hierarchy.linkage(
                    condensed_distances, method="centroid"
                )

                partition = scipy.cluster.hierarchy.fcluster(
                    linkage, distance_threshold, criterion="distance"
                )

                clusters: dict[int, list[int]] = defaultdict(list)

                for i, cluster_id in enumerate(partition):
                    clusters[cluster_id].append(i)

                squared_distances = condensed_distances**2
                for cluster in clusters.values():
                    if len(cluster) > 1:
                        scores = confidences(cluster, squared_distances, N)
                        yield tuple(i_to_id[i] for i in cluster), scores  # type: ignore[misc]

            else:
                ((ids, score),) = sub_graph
                if score > threshold:
                    yield tuple(ids), (score,) * 2


def connected_components(edgelist: Scores, max_components: int) -> Generator[Scores]:
    """
    Remplacement drop-in de dedupe.clustering.connected_components.

    Comportement identique à l'original, sans l'étape tempfile/memmap qui
    écrivait le gros fichier sur disque. dedupe utilisait un memmap pour
    pouvoir ajouter une colonne "label" à une edgelist potentiellement
    énorme et déjà memmapée sans doubler la RAM utilisée. Pour ~30M arêtes
    (quelques centaines de Mo à 1-2 Go une fois labellisées), le faire
    directement en RAM est plus simple et plus rapide.
    """
    if len(edgelist) == 0:
        return

    labeled = numpy.empty(
        edgelist.shape, dtype=edgelist.dtype.descr + [("label", "int32")]
    )
    labeled["pairs"] = edgelist["pairs"]
    labeled["score"] = edgelist["score"]

    yield from _connected_components(labeled, max_components)


def _connected_components(edgelist: Scores, max_components: int) -> Generator[Scores]:
    component_stops = _fast_union_find(edgelist)

    start = 0
    for stop in component_stops:
        sub_graph = edgelist[start:stop]
        n_edges = stop - start
        start = stop

        needs_filtering = False
        # first we find the upper bound of the
        # number of components given the edgelist
        upper_bound_components = n_edges + 1
        if upper_bound_components > max_components:
            # which we can refine using a more expensive operation
            # if it's possible we have too many components
            n_components = len(numpy.unique(sub_graph["pairs"]))
            if n_components > max_components:
                needs_filtering = True

        if needs_filtering:
            min_score = numpy.min(sub_graph["score"])
            min_score_logit = numpy.log(min_score) - numpy.log(1 - min_score)
            threshold = 1 / (1 + numpy.exp(-min_score_logit - 1))
            logger.warning(
                f"A component contained {n_components} elements. "
                f"Components larger than {max_components} are "
                "re-filtered. The threshold for this "
                f"filtering is {threshold}"
            )
            # slices of memmaped arrays are also memmaped arrays,
            # which is what we want. The components should
            # already sorted by score so we can slice as oppose
            # to selecting like `sub_graph[sub_graph['score'] >
            # threshold]`, which would lead to an in memory copy being
            # made
            cut_point = numpy.searchsorted(sub_graph["score"], threshold)
            filtered_sub_graph = sub_graph[max(cut_point, 2) :]

            for sub_graph in _connected_components(filtered_sub_graph, max_components):
                yield sub_graph[["pairs", "score"]]
        else:
            yield sub_graph[["pairs", "score"]]


def _fast_union_find(scored_pairs: numpy.ndarray) -> numpy.ndarray:
    """
    Remplacement drop-in de dedupe.clustering.union_find.

    Même contrat que l'original :
      - remplit scored_pairs["label"] en place avec un id de composante par arête
      - trie scored_pairs en place par ("label", "score") croissant
      - retourne les tailles cumulées par composante (component_stops)

    mais implémenté via scipy.sparse.csgraph.connected_components (compilé,
    O(V+E)) plutôt que la boucle Python + numpy.unique-par-fusion de dedupe.
    """
    pairs = scored_pairs["pairs"]
    n_edges = len(scored_pairs)

    # On ramène les IDs (potentiellement des chaînes longues) à des indices
    # entiers compacts, uniquement pour la durée de l'appel scipy. Rien
    # n'est écrit sur disque et les IDs d'origine ne sont jamais dupliqués
    # au-delà de ce tableau temporaire.
    node_ids, node_idx_flat = numpy.unique(pairs.ravel(), return_inverse=True)
    node_idx = numpy.asarray(node_idx_flat).reshape(pairs.shape)
    n_nodes = len(node_ids)

    graph = sp.csr_matrix(
        (
            numpy.ones(n_edges, dtype=numpy.int8),
            (node_idx[:, 0], node_idx[:, 1]),
        ),
        shape=(n_nodes, n_nodes),
    )

    _, node_labels = _scipy_connected_components(graph, directed=False)

    edge_labels = node_labels[node_idx[:, 0]].astype("int32")
    scored_pairs["label"] = edge_labels

    # Même heuristique que dedupe : tri stable en dessous de 2.5M lignes
    # (le tri stable coûte ~n/2 en mémoire de travail)
    if n_edges > 2_500_000:
        scored_pairs.sort(order=("label", "score"))
    else:
        scored_pairs.sort(order=("label", "score"), kind="stable")

    return numpy.cumsum(numpy.unique(scored_pairs["label"], return_counts=True)[1])


# ---------------------------------------------------------------------------
# Script de validation : vérifie que le patch produit EXACTEMENT le même
# résultat que l'implémentation d'origine de dedupe, sur des données
# synthétiques. À lancer avant de déployer le patch en prod.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import dedupe.clustering as dc

    logging.basicConfig(level=logging.INFO)
    rng = numpy.random.default_rng(0)

    N_RECORDS = 200_000
    N_EDGES = 400_000

    def make_edgelist():
        a = rng.integers(0, N_RECORDS, N_EDGES)
        b = rng.integers(0, N_RECORDS, N_EDGES)
        mask = a != b
        a, b = a[mask], b[mask]
        lo, hi = numpy.minimum(a, b), numpy.maximum(a, b)
        pairs = numpy.unique(numpy.stack([lo, hi], axis=1), axis=0)
        scores = rng.uniform(0.5, 1.0, size=len(pairs)).astype("f4")
        edgelist = numpy.empty(len(pairs), dtype=[("pairs", "i4", 2), ("score", "f4")])
        edgelist["pairs"] = pairs
        edgelist["score"] = scores
        return edgelist

    edgelist = make_edgelist()
    print(f"{len(edgelist)} arêtes synthétiques générées")

    # --- run avec l'implémentation d'origine de dedupe ---
    t0 = time.perf_counter()
    original_clusters = sorted(
        tuple(sorted(ids)) for ids, scores in dc.cluster(edgelist.copy(), threshold=0.5)
    )
    t_original = time.perf_counter() - t0
    print(f"dedupe original : {t_original:.2f}s, {len(original_clusters)} clusters")

    # --- run avec le patch ---
    t0 = time.perf_counter()
    patched_clusters = sorted(
        tuple(sorted(ids)) for ids, scores in cluster(edgelist.copy(), threshold=0.5)
    )
    t_patched = time.perf_counter() - t0
    print(f"dedupe patché   : {t_patched:.2f}s, {len(patched_clusters)} clusters")

    assert (
        original_clusters == patched_clusters
    ), "Les clusters diffèrent entre l'implémentation d'origine et la version patchée !"
    print(
        f"OK : résultats identiques. Accélération : x{t_original / max(t_patched, 1e-9):.1f}"
    )

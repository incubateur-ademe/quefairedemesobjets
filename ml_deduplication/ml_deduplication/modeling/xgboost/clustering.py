import logging

logger = logging.getLogger(__name__)

DEFAULT_SHOULD_BE_DIFFERENT_FIELDS = ("source_id",)
DEFAULT_SHOULD_BE_EQUAL_FIELDS = ("acteur_type_id",)

FEATURES_COLUMNS_NAMES = (
    "nom_clean_dist",
    "adresse_clean_distance",
    "ville_clean_dist",
    "siren_match",
    "siret_match",
    "telephone_match",
    "code_commune_insee_match",
    "code_postal_match",
    "departement_match",
)


class ConstrainedUnionFind:
    """
    Structure Union-Find optimisée qui refuse la fusion de deux clusters
    si cela viole les règles métier strictes (anti-transitivité des conflits).

    Args:
        entity_attributes: Dictionnaire {entity_id: {field_name: value}}
        should_be_different_fields: Liste des champs qui doivent être uniques dans un cluster.
        should_be_equal_fields: Liste des champs qui doivent être identiques dans un cluster.
    """

    def __init__(
        self,
        entity_attributes: dict,
        should_be_different_fields: list[str],
        should_be_equal_fields: list[str],
    ):
        self.parent = {}
        # Stocke les valeurs uniques par champ pour chaque racine de cluster
        # Format: {root_id: {field_name: set_of_values}}
        self.cluster_attrs = {}

        self._diff_fields = list(should_be_different_fields)
        self._eq_fields = list(should_be_equal_fields)
        self._all_tracked_fields = list(set(self._diff_fields + self._eq_fields))

        self.refused_unions_count = 0
        for eid, attrs in entity_attributes.items():
            self.parent[eid] = eid
            self.cluster_attrs[eid] = {}

            for field in self._all_tracked_fields:
                val = attrs.get(field)
                # On ignore les valeurs nulles pour ne pas créer de faux conflits
                if val is not None:
                    self.cluster_attrs[eid][field] = {val}
                else:
                    self.cluster_attrs[eid][field] = set()

    def find(self, i):
        # Compression de chemin pour une performance quasi O(1)
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def _are_values_compatible(self, v1, v2, field_name: str) -> bool:
        """Vérifie si deux valeurs sont compatibles pour un champ 'doit être égal'."""
        if v1 == v2:
            return True

        # Cas particulier métier : acteur_type_id 3 et 4 sont compatibles
        if field_name == "acteur_type_id" and {v1, v2} == {3, 4}:
            return True

        return False

    def union(self, i, j) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i == root_j:
            return False  # Déjà dans le même cluster

        # --- 1. VÉRIFICATION DES CONTRAINTES "DOIT ÊTRE DIFFÉRENT" ---
        for field in self._diff_fields:
            set_i = self.cluster_attrs[root_i].get(field, set())
            set_j = self.cluster_attrs[root_j].get(field, set())

            # Si les deux clusters ont des valeurs non-null pour ce champ et qu'elles se chevauchent
            if set_i and set_j and not set_i.isdisjoint(set_j):
                self.refused_unions_count += 1
                return (
                    False  # Conflit détecté (ex: même source_id), on refuse la fusion
                )

        # --- 2. VÉRIFICATION DES CONTRAINTES "DOIT ÊTRE ÉGAL" ---
        for field in self._eq_fields:
            set_i = self.cluster_attrs[root_i].get(field, set())
            set_j = self.cluster_attrs[root_j].get(field, set())

            if not set_i or not set_j:
                continue  # Si l'un des deux est null, pas de conflit de ce côté

            # On vérifie toutes les combinaisons possibles entre les valeurs des deux clusters
            # (En pratique, ces sets sont très petits, souvent de taille 1, donc O(1))
            for v1 in set_i:
                for v2 in set_j:
                    if not self._are_values_compatible(v1, v2, field):
                        self.refused_unions_count += 1
                        return False  # Conflit détecté, on refuse la fusion

        # --- 3. FUSION VALIDE ---
        self.parent[root_i] = root_j

        # Mise à jour des attributs du cluster racine (root_j absorbe root_i)
        for field in self._all_tracked_fields:
            set_i = self.cluster_attrs[root_i].get(field, set())
            if field not in self.cluster_attrs[root_j]:
                self.cluster_attrs[root_j][field] = set()
            self.cluster_attrs[root_j][field].update(set_i)

        return True

    def get_clusters(self) -> dict:
        """Retourne un mapping {entity_id: cluster_root_id}"""
        return {eid: self.find(eid) for eid in self.parent}

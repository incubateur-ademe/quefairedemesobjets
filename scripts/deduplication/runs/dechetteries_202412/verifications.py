"""
Fichier servant à définir des clusters de vérifications avec
changements attendus pour le fichier de déduplication en cours.

Ceci est pas facile à tourné en test unitaire car
il faudrait mocker l'état de la base = travail considérable
à l'heure actuelle.

En revanche les tests ci-dessous demeurrent utiles
en executant le script en mode DRY RUN (càd pas de modifications DB)
pour vérifier que tous les changements sont conformes
avant de les appliquer, puis en lançant le script en mode normal
pour appliquer les changements.

"""

from models.change import Change

# Mapping de cluster_id -> list des changements attendus
RUN_CLUSTER_IDS_TO_CHANGES: dict[str, list[Change]] = {
    # cluster sans parent
    "01100_1_1": [
        Change(
            operation="parent_create",
            acteur_id="a2a5e451-faf9-56d9-b704-1eea94530810",
        ),
        Change(
            operation="child_create_revision", acteur_id="ademe_sinoe_decheteries_3814"
        ),
        Change(operation="child_create_revision", acteur_id="corepile_01-COL-0024_01"),
        Change(operation="child_create_revision", acteur_id="ecomaison_2046279"),
    ],
    # cluster à 1 parent existant
    "01110_1_1": [
        Change(
            operation="parent_choose", acteur_id="45a04695-b796-4f20-b4fc-c7c7af8d29bf"
        ),
        Change(
            operation="child_create_revision", acteur_id="ademe_sinoe_decheteries_2919"
        ),
        Change(operation="child_create_revision", acteur_id="ecomaison_2004328"),
    ],
    # Cluster avec 1 parent à 3 enfants (choisi) et un parent à 2 enfant (delete)
    "01250_2_1": [
        Change(
            operation="parent_choose", acteur_id="025549d3-89f4-400a-967c-bccd4840bdf8"
        ),
        Change(
            operation="parent_delete", acteur_id="6afbd3c2-ee5b-4b76-a853-2f0b08dd5c64"
        ),
        Change(
            operation="child_create_revision", acteur_id="ademe_sinoe_decheteries_43164"
        ),
        Change(operation="child_create_revision", acteur_id="ecomaison_2020724"),
    ],
    # Cluster avec 2 parents à 2 enfants chacun, le parent
    # sera pris par ordre d'apparition dans le cluster
    "74130_3_1": [
        Change(
            operation="parent_choose", acteur_id="4c5d0509-16be-4cca-86c0-56e049f05908"
        ),
        Change(
            operation="parent_delete", acteur_id="66ec3d8a-f7b8-4776-9c71-df402306578b"
        ),
        Change(
            operation="child_create_revision",
            acteur_id="ademe_sinoe_decheteries_109819",
        ),
        Change(
            operation="child_create_revision",
            acteur_id="ecomaison_2042944",
        ),
    ],
    # Clusters avec aucun parent (donc 1 à créer), et certains enfants déjà en révision
    "94170_1_1": [
        Change(
            operation="parent_create", acteur_id="573107b7-a79f-5d48-982a-c878d0f7a62b"
        ),
        # déjà en révision, à mettre à jour
        Change(
            operation="child_update_revision",
            acteur_id="ecosystem_EEE-ecosystem-C-1041207",
        ),
        Change(
            operation="child_create_revision", acteur_id="ademe_sinoe_decheteries_27136"
        ),
        Change(operation="child_create_revision", acteur_id="corepile_94-COL-0013_04"),
        Change(operation="child_create_revision", acteur_id="ecodds_FD4070"),
        Change(
            operation="child_create_revision",
            acteur_id="refashion_TLC-REFASHION-PAV-3303623",
        ),
    ],
}

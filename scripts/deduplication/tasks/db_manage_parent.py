"""
Tâche pour la gestion d'un parent (choix du parent, création avec UUID si manquant
ou mise à jour si existant)
"""

import uuid
from itertools import chain

from django import forms
from django.db.models import Model
from django.forms.models import model_to_dict
from rich import print

from qfdmo.models.acteur import RevisionActeur
from scripts.deduplication.models.acteur_map import ActeurMap
from scripts.deduplication.models.change import Change
from scripts.deduplication.utils.db import db_source_ids_by_code_get


def parent_id_generate(ids: list[str]) -> str:
    """
    Génère un UUID (pour l'identifiant_unique parent) à partir
    de la liste des identifiants des enfants du cluster.
    Le UUID généré doit être:
    - déterministe (même entrée donne même sortie)
    - ordre-insensible (sort automatique)

    Args:
        ids: liste des identifiants uniques des enfants

    Returns:
        str: nouvel identifiant_unique du parent
    """
    combined = ",".join(sorted(ids))
    parent_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, combined))
    print("parent_id_generate", f"{ids=}", f"{parent_id=}")
    return parent_id


def acteurs_dict_to_list_of_dicts(acteurs_maps: list[ActeurMap]) -> list[dict]:
    """Extrait tous les acteurs sous tous leurs états (revision -> base)
    pour les mettre dans une liste de dict, afin de faciliter la génération
    de la donnée parent reconciliée

    Args:
        acteurs_maps: liste d'acteurs sous forme ActeurMap

    Returns:
        acteurs_dicts: liste de dict des acteurs
    """

    # sort values of acteurs_map by children_count
    # flatten/pick all non-None revision, base values
    acteurs_maps = sorted(acteurs_maps, key=lambda x: x.children_count, reverse=True)
    acteurs_list = list(
        # On écrase la liste de liste en 1 seule liste
        chain.from_iterable(
            [
                # Pour chaque acteur, on récupère dans l'ordre les
                # objets revision, base si non None
                [
                    acteur.table_states[k]  # type: ignore
                    for k in ["revision", "base"]
                    if acteur.table_states[k] is not None  # type: ignore
                ]
                for acteur in acteurs_maps
            ]
        )
    )
    """
    [
        acteur["table_states"][k]
        for k in ["revision", "base"]
        if acteur["table_states"][k] is not None
    ]
    """
    # Convertion de la liste des objets Django en liste de dict
    acteurs_dicts = [
        model_to_dict(
            item,
            fields=[
                field.name
                for field in item._meta.get_fields()
                # on the prend que les champs concrets et non many_to_many
                if field.concrete and not field.many_to_many  # type: ignore
            ],
        )
        for item in acteurs_list
    ]

    # FIXME: voir si il est possible pour Django de donner à ces champs le même nom
    # qu'en DB pour éviter d'avoir à les renommer vers _id
    for acteur in acteurs_dicts:
        acteur["source_id"] = acteur.pop("source")
        acteur["acteur_type_id"] = acteur.pop("acteur_type")
        # Problème silimaire mais + compliqué puisque
        # django le rattache à un autre modèle: étant donné qu'on ne se
        # sert pas du champs parent_id pour générer le parent, on le supprime
        if "parent" in acteur:
            del acteur["parent"]

    return acteurs_dicts


def parent_get_data_from_acteurs(
    acteurs: list[dict],
    source_ids_by_code: dict,
    sources_preferred_ids,
    validation_model: Model,
) -> tuple[dict, dict]:
    """
    Récupération des données d'acteurs pour l'utilisation dans un parent. Pour l'instant
    la logique est primitive de choisir selon une liste de sources préférées. A l'avenir
    on pourrait imaginer de réconcilier à la majorité ou autre logique plus avancée.

    Args:
        acteurs: list d'acteurs sous forme de dict
        sources_preferred_ids: liste des id des sources préférées, dans l'ordre de prio
        validation_model: modèle django pour valider la donnée

    Returns:
        parent_dict: donnée parent sous forme de dict
        sources_codes_picked: mapping des champs et sources choisies
    """
    # TODO: revoir les règles d'inclusion/exclusion pour la prochaine
    # dédup pour le rendre plus flexible avec l'acteur_type_id
    # - entrée de mapping = acteur_type_id x champ
    # - sortie de mapping = liste de sources à inclure/exclure
    if any(x["acteur_type_id"] not in (None, 7) for x in acteurs):
        raise NotImplementedError(
            """Règles inclusion/exclusion pour la dédup déchetteries uniquement,
            revoir avec Christian avec la prochaine dédup"""
        )

    source_codes_by_id = {v: k for k, v in source_ids_by_code.items()}
    parent_dict = {}
    sources_codes_picked = {}
    # Mapping d'inclusion de source spécifique à certains champs
    # TODO: les 2 mapping doivent être exclusif
    field_source_codes_priority = {
        "nom": ["COREPILE", "ALIAPUR"],
        "location": ["REFASHION"],
    }
    # Mapping d'exclusion de source spécifique à certains champs
    field_source_codes_exclusion = {
        "nom": ["REFASHION"],
        "nom_commercial": ["REFASHION", "ECODDS"],
        "siret": ["REFASHION"],
        "siren": ["REFASHION"],
        "telephone": ["REFASHION"],
    }
    # Ignore les champs d'identifications acteurs
    # car il doivent tous restés vides (générés ultérieurement)
    keys_to_ignore = [
        "identifiant_unique",
        "identifiant_externe",
        "parent_id",
        "source_id",
        # Déjà géré par Django
        "modifie_le",
        # Soit on garde la valeur historique, ou soit pour un nouveau
        # parent c'est géré par Django
        "cree_le",
    ]

    def results_update(field, value, acteur):
        """utilitaire MAJ de parent_dict et sources_codes_picked
        + some debug prints pour éviter de se répéter sur les
        2 boucles"""
        source_id = acteur["source_id"]
        source_code = source_codes_by_id.get(source_id)
        acteur_id = acteur["identifiant_unique"]
        parent_dict[field] = value
        sources_codes_picked[field] = source_code
        print(f"\t✅ {field=} {value=}")
        print(f"\t\t via {source_code=} {acteur_id=}")

    # ------------------------------------
    # Boucle 1: données via inclusion/exclusion champs/sources spécéfiques
    # ------------------------------------
    print("parent_get_data_from_acteurs: boucle 1")
    for field, source_codes_inclusion in field_source_codes_priority.items():
        source_codes_exlusion = field_source_codes_exclusion.get(field, [])
        # acteurs candidats pour le champ
        cands = sorted(
            [
                x
                for x in acteurs
                if x["source_id"] is not None
                and source_codes_by_id[x["source_id"]] in source_codes_inclusion
                and source_codes_by_id[x["source_id"]] not in source_codes_exlusion
                and x[field] is not None
            ],
            key=lambda x: source_codes_inclusion.index(
                source_codes_by_id[x["source_id"]]
            ),
        )
        acteur = next(iter(cands), None)
        if acteur is not None:
            results_update(field, acteur[field], acteur)

    # ------------------------------------
    # Boucle 2: données restantes via les sources préférées
    # ------------------------------------
    # Ordonner acteurs sur source_id dans l'ordre de sources_preferred_ids
    # et les autres acteurs par défaut après
    acteurs = sorted(
        acteurs,
        key=lambda x: (
            # plus la source est haute dans la liste de sources préférées,
            # plus sont index est bas = plus haute est la priorité
            sources_preferred_ids.index(x["source_id"])
            if x["source_id"] in sources_preferred_ids
            # cas non présent dans sources_preferred_ids, on retourne
            # l'index le plus haut possible = priorité la plus basse
            else len(sources_preferred_ids)
        ),
    )
    print("parent_get_data_from_acteurs: boucle 2")
    email_field = forms.EmailField()
    for acteur in acteurs:
        source_code = source_codes_by_id.get(acteur["source_id"])
        # Précédent parent non selectionné comme parent pour le nouveau
        # cluster, on veut pas prendre le risque de réutiliser ces données
        if source_code is None:
            continue
        for field, value in acteur.items():
            source_codes_exlusion = field_source_codes_exclusion.get(field, [])
            if (
                field not in keys_to_ignore
                and value is not None
                and parent_dict.get(field) is None
                and source_code not in source_codes_exlusion
            ):
                # TODO: voir si il y aurait une façon plus élégante
                # d'automatiquement supprimer toutes les données invalides
                # plutôt que de le faire manuellement champ par champ.
                # Ceci est en lien avec le problème de présence de mauvais
                # emails dans la DB, qui empêche la réutilisation du
                # modèle django car .save() appelle .full_clean() qui crash
                if field == "email":
                    try:
                        email_field.clean(value)
                    except forms.ValidationError:
                        continue
                results_update(field, value, acteur)
    # Et on met la source_id à None car c'est une création de notre
    # part, donc il ne correspond pas à une source existante
    parent_dict["source_id"] = None

    # On s'assure que la donnée est compatible avec le modèle de révision
    validation_model(**parent_dict)  # type: ignore
    # On retourne la données sous forme de dict pour qu'elle puisse
    # être utilisée soit sur un parent existant (update) soit pour créer un
    # nouveau parent (insert)
    return parent_dict, sources_codes_picked


def db_manage_parent(
    acteurs_maps: list[ActeurMap],
    sources_preferred_ids: list[int],
    is_dry_run: bool,
) -> tuple[str, Change]:
    """Gestion de tous les aspects du parent:
     - préparation de sa donnée
     - choix du parent
     - MAJ DB

    Args:
        acteurs_map: mapping des acteurs id: {id, table_states, children_count}
        sources_preferred_ids: IDs des sources préférées pour la fusion des données,
                              listées dans l'ordre de préférence
        is_dry_run: mode test ou non

    Returns:
        parent_id: identifiant_unique du parent (existing ou UUID généré)
        change: changement effectué
    """
    print("PREPARATION DE LA DONNEE PARENT:")
    # Cette donnée nous est utile quel que soit le parent choisi
    # si existant: on le met à jour
    # si à créer: on utilise cette donnée pour créer le parent
    identifiants_uniques = [x.identifiant_unique for x in acteurs_maps]
    acteurs_dicts = acteurs_dict_to_list_of_dicts(acteurs_maps)
    # print(f"{acteurs_list=}")
    parent_data, _ = parent_get_data_from_acteurs(
        acteurs=acteurs_dicts,
        source_ids_by_code=db_source_ids_by_code_get(),
        sources_preferred_ids=sources_preferred_ids,
        validation_model=RevisionActeur,  # type: ignore
    )
    print(f"{parent_data=}")

    print("CHOIX DU PARENT:")
    # Filtre acteurs_map pour ne garder que les valeurs avec children_count>0
    # si parents existant, on prend celui avec le plus d'enfants
    parents_list = [x for x in acteurs_maps if x.children_count > 0]
    # Parent(s) existant(s)
    if parents_list:
        parent_chosen = max(parents_list, key=lambda x: x.children_count)
        parent_id = parent_chosen.identifiant_unique
        change = Change(operation="parent_choose", acteur_id=parent_id)
        print("\t1) Priorité au parent existant avec le + d'enfant:")
        print(f"{parent_chosen.identifiant_unique=}")
        parent = parent_chosen.table_states["revision"]
        print("\t\t - mise à jour du parent existant:")
        for k, val_new in parent_data.items():
            val_current = getattr(parent, k)
            if val_new is not None and val_current is None:
                print("\t\t\t", f"{k=}", f"{val_current=}", f"{val_new=}")
                setattr(parent, k, val_new)
        if is_dry_run:
            print("\t\tDB: pas de modif en dry run ✋")
            pass
        else:
            parent.save()

    else:
        # Sinon il faut en créer un
        print("\t2) Pas de parent existant, à créer")
        parent_id = parent_id_generate(identifiants_uniques)
        change = Change(operation="parent_create", acteur_id=parent_id)
        parent = RevisionActeur(**parent_data)
        parent.identifiant_unique = parent_id
        print(f"\t\t{parent=}")
        if is_dry_run:
            print("\t\tDB: pas de modif en dry run ✋")
            pass
        else:
            parent.save_as_parent()

    return parent_id, change

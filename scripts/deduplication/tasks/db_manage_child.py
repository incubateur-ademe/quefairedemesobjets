"""
Tâche pour la gestion des enfants d'un cluster
"""

from rich import print

from qfdmo.models.acteur import Acteur, RevisionActeur
from scripts.deduplication.models.acteur_map import ActeurMap
from scripts.deduplication.models.change import Change


def db_manage_child(
    child: ActeurMap, parent_id: str, is_dry_run: bool = True
) -> Change:
    """Gestion DB de l'enfant (insert ou vérification dans les tables)

    Args:
        db_engine: workaround pour faire de l'update DB manuelle
        child: ActeurMap d'un enfant
        parent_id: identifiant_unique du parent
        is_dry_run: mode test

    Returns:
        Change: objet de changement
    """
    print("\nGESTION DE L'ENFANT", f"{child=}", f"{parent_id=}")

    # D2: Est-ce que l'acteur était déjà un parent? = OUI
    # alors on doit rediriger les FKs vers le nouveau parent
    # et supprimer la révision de cette ancien parent
    if child.is_parent:
        print("\t🔴 Enfant ancien parent: changement FKs et suppression de sa revision")
        change = Change(operation="parent_delete", acteur_id=child.identifiant_unique)
        if is_dry_run:
            print("DB: pas de modif en dry run ✋")
            pass
        else:
            # On commence par migrer tous les enfants existants vers le nouveau parent
            RevisionActeur.objects.filter(parent_id=child.identifiant_unique).update(
                parent_id=parent_id
            )
            # Puis on supprime l'ancien parent
            RevisionActeur.objects.filter(
                identifiant_unique=child.identifiant_unique
            ).delete()
            print("DB: modifiée via Django ✅")
    # D2: Est-ce que l'acteur était déjà un parent? = NON
    else:
        print("\t🟠 Enfant NON parent")
        # D3: Est-ce que l'acteur était déjà une revision? = OUI
        # alors on doit mettre à jour le parent_id
        if child.table_states["revision"] is not None:
            change = Change(
                operation="child_update_revision", acteur_id=child.identifiant_unique
            )
            print(f"\t\t🟠 avec une révision existante: MAJ {parent_id=}")
            print("\t🟠 Enfant pas parent mais dans révision: MAJ du parent_id")
            if is_dry_run:
                print("DB: pas de modif en dry run ✋")
            else:
                RevisionActeur.objects.filter(
                    identifiant_unique=child.identifiant_unique
                ).update(parent_id=parent_id)
                print("DB: modifiée via Django ✅")
        # D3: Est-ce que l'acteur était déjà une revision? = NON
        # alors on doit créer une révision avec le parent_id
        else:
            print("\t\t🔴 sans révision: créer revision avec parent_id")
            change = Change(
                operation="child_create_revision", acteur_id=child.identifiant_unique
            )
            if is_dry_run:
                print("DB: pas de modif en dry run ✋")
                pass
            else:
                # Création de la révision si besoin (càd si l'acteur
                # n'existe que dans la table de base qfdmo_acteur)
                acteur = Acteur.objects.get(identifiant_unique=child.identifiant_unique)
                acteur_rev = acteur.get_or_create_revision()
                acteur_rev.save()
                print(f"{acteur_rev.identifiant_unique=}")
                RevisionActeur.objects.filter(
                    identifiant_unique=child.identifiant_unique
                ).update(parent_id=parent_id)
                print("DB: modifiée via Django ✅")

        if not is_dry_run:
            # Fin des diverses cas enfants: quels que soient les cas rencontrés,
            # on devrait toujours avoir 1 révision enfant avec le parent_id
            # qui pointe vers le bon parent
            print("\t🔎 Vérification changement enfant en db:")
            revision = RevisionActeur.objects.get(pk=child.identifiant_unique)
            print("\t\t- révision existe belle et bien: ✅")
            parent_id_db = revision.parent.identifiant_unique  # type: ignore
            if parent_id_db != parent_id:
                raise Exception(f"Erreur: {parent_id_db=} différent de {parent_id=}")
            print(f"\t\t- {parent_id_db=} pointe bien vers bon parent: ✅")

    return change

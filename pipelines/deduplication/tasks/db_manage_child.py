"""
Tâche pour la gestion des enfants d'un cluster
"""

from rich import print
from sqlalchemy.engine import Engine

from pipelines.deduplication.models.acteur_map import ActeurMap
from pipelines.deduplication.models.change import Change
from pipelines.deduplication.utils.db import db_modify
from qfdmo.models.acteur import Acteur, RevisionActeur


def db_manage_child(
    db_engine: Engine, child: ActeurMap, parent_id: str, is_dry_run: bool = True
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
        sql_update = f"""UPDATE qfdmo_revisionacteur
            SET parent_id = '{parent_id}'
            WHERE parent_id = '{child.identifiant_unique}';"""
        db_modify(db_engine, sql_update, is_dry_run)

        sql_delete = f"""DELETE FROM qfdmo_revisionacteur
            WHERE identifiant_unique = '{child.identifiant_unique}';"""
        db_modify(db_engine, sql_delete, is_dry_run)
        change = Change(operation="parent_delete", acteur_id=child.identifiant_unique)
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
            # TODO: convertir ci-dessous en requête Django
            print("\t🟠 Enfant pas parent mais dans révision: MAJ du parent_id")
            sql_update = f"""UPDATE qfdmo_revisionacteur
                SET parent_id = '{parent_id}'
                WHERE identifiant_unique = '{child.identifiant_unique}';"""
            db_modify(db_engine, sql_update, is_dry_run)
        # D3: Est-ce que l'acteur était déjà une revision? = NON
        # alors on doit créer une révision avec le parent_id
        else:
            print("\t\t🔴 sans révision: créer revision avec parent_id")
            change = Change(
                operation="child_create_revision", acteur_id=child.identifiant_unique
            )
            if is_dry_run:
                print("DB: pas de modif en mode test ✋")
                pass
            else:
                acteur = Acteur.objects.get(identifiant_unique=child.identifiant_unique)
                acteur_rev = acteur.get_or_create_revision()
                acteur_rev.save()
                print(f"{acteur_rev.identifiant_unique=}")
                sql_update = f"""UPDATE qfdmo_revisionacteur
                    SET parent_id = '{parent_id}'
                    WHERE identifiant_unique = '{child.identifiant_unique}';"""
                db_modify(db_engine, sql_update, is_dry_run)
                # Ne pas utiliser l'endpoint ci-dessous, nécessite une authentification
                # Django pas documentée ET bcp plus difficile de savoir si ça a marché
                # que d'utiliser les modèles Django de base
                # get_or_create_revisionacteur(django_url, child.identifiant_unique)
                print("DB: modifié via API ✅")
                # Fin des diverses cas: quels que soient les cas rencontrés,
                # on devrait toujours avoir 1 révision avec le parent_id
                # qui pointe vers le parent
                print("\t🔎 Vérification changement enfant en db:")
                revision = RevisionActeur.objects.get(pk=child.identifiant_unique)
                print("\t\t- révision existe belle et bien: ✅")
                parent_id_db = revision.parent.identifiant_unique  # type: ignore
                if parent_id_db != parent_id:
                    raise Exception(
                        f"Erreur: {parent_id_db=} différent de {parent_id=}"
                    )
                print(f"\t\t- {parent_id_db=} est correct: ✅")

    return change

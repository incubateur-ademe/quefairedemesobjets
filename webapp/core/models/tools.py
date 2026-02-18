import logging

from django.db import connections
from utils.django import DJANGO_WH_CONNECTION_NAME

logger = logging.getLogger(__name__)


def compare_model_vs_table(cls, table_name: str) -> bool:

    def are_fields_matched(db_type, model_type):
        logger.info(f"Comparing {db_type} with {model_type}")
        return (
            db_type == model_type
            # AutoField is a IntegerField
            or (db_type == "IntegerField" and model_type == "AutoField")
            # hamp 'id': Model (BigAutoField) -> DB (BigIntegerField)
            or (db_type == "BigIntegerField" and model_type == "BigAutoField")
            # PointField is a GeometryField
            or (
                db_type in ["PointField", "GeometryField"]
                and model_type == "PointField"
            )
        )

    connection = connections[DJANGO_WH_CONNECTION_NAME]

    with connection.cursor() as cursor:

        table_info = connection.introspection.get_table_list(cursor)
        for table in table_info:
            logger.info(f"Table: {table}")
        if not any(table.name == table_name for table in table_info):
            logger.error(f"La table {table_name} n'existe pas")
            return False

        table_description = connection.introspection.get_table_description(
            cursor, table_name
        )
        db_columns = {
            info.name: {
                "type": connection.introspection.get_field_type(info.type_code, info),
                "null_ok": info.null_ok,
                "display_size": (
                    info.display_size
                    if info.display_size and info.display_size > 0
                    else None
                ),
            }
            for info in table_description
        }

        # Récupérer les champs du modèle
        model_fields = cls._meta.fields

        # Comparer les champs
        logger.info(f"Comparaison du modèle {cls.__name__} vs la table {table_name}:")

        all_fields_match = True
        # Vérifier les champs du modèle présents dans la table
        for field in model_fields:
            # Gestion spéciale pour les ForeignKey
            if field.get_internal_type() == "ForeignKey":
                field_name = f"{field.db_column or field.name}_id"
            else:
                field_name = field.db_column or field.name

            if field_name in db_columns:
                if field.get_internal_type() == "ForeignKey":
                    model_type = field.related_model._meta.pk.get_internal_type()
                    logger.info(f"Field {field_name} is a ForeignKey to {model_type}")
                    logger.info(f"Field {field.related_model._meta.pk}")
                else:
                    model_type = field.get_internal_type()

                db_type = db_columns[field_name]["type"]

                field_matches = are_fields_matched(db_type, model_type)
                if not field_matches:
                    logger.error(
                        f"✗ Champ '{field_name}' ({db_type}) n'a pas la même"
                        " configuration de type : "
                        f"DB : {db_type} vs Model : {model_type}"
                    )
                all_fields_match &= field_matches

                # No check of not Null constraint because DBT doesn't handle this
                # constraint

                # Check length of CharFields and TextFields
                if (
                    hasattr(field, "max_length")
                    and db_type in ["CharField", "TextField"]
                    and db_columns[field_name]["display_size"] != field.max_length
                ):
                    all_fields_match = False
                    logger.error(
                        f"✗ Champ '{field_name}' ({db_type}) n'a pas la même"
                        " configuration de longueur : "
                        f"DB : {db_columns[field_name]['display_size']}"
                        f" vs Model : {field.max_length}"
                    )

                # # Check db_default

                status = "✓" if field_matches else "✗"
                logger.info(
                    f"{status} Champ '{field_name}': "
                    f"Model ({model_type}) -> DB ({db_type})"
                )

            else:
                all_fields_match = False
                logger.error(f"✗ Champ '{field_name}' manquant dans la table")

        # Vérifier les colonnes de la table non présentes dans le modèle
        model_db_columns = {
            (
                f"{f.db_column or f.name}_id"
                if f.get_internal_type() == "ForeignKey"
                else f.db_column or f.name
            )
            for f in model_fields
        }
        for db_column in db_columns:
            if db_column not in model_db_columns:
                logger.warning(
                    f"! Colonne '{db_column}' présente en DB "
                    f"mais pas dans le modèle"
                )

        # Vérification des relations M2M
        cls_table = cls._meta.db_table
        for field in cls._meta.many_to_many:
            logger.info(f"\nVérification des relations Many-to-Many : {field.name}")
            through_model = field.remote_field.through
            through_table = through_model._meta.db_table
            through_table = through_table.replace(cls_table, table_name)
            all_fields_match &= compare_model_vs_table(
                through_model,
                through_table,
            )

        return all_fields_match

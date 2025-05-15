"""Utilities to work with Django from Airflow

🟠 For Django to work in Airflow, the various django
folders (e.g. qfdmo/, data/ etc...) must be mounted
on the Airflow container.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from utils import logging_utils as log

logger = logging.getLogger(__name__)


def django_add_to_sys_path() -> None:
    """
    Adds Django project root to sys.path, based on current file path
    """
    django_root = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, django_root)


def django_settings_to_dict() -> dict:
    """Returns useful information from settings
    as a JSON-compatible dict to help us debug
    (e.g. when setting up e2e Airflow tests)"""
    from django.conf import settings

    return {
        "DATABASES": {
            alias: {
                "HOST": config.get("HOST", ""),
                "PORT": config.get("PORT", ""),
                "NAME": config.get("NAME", ""),
            }
            for alias, config in settings.DATABASES.items()
        }
    }


def django_setup_full() -> None:
    """Full init of our Django environment"""
    django_add_to_sys_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.airflow_settings")

    import django

    django.setup()


def django_conn_to_sqlalchemy_engine(using="default"):
    """Return a SQLAlchemy engine from a Django connection"""
    from django.db import connections
    from sqlalchemy import create_engine

    conn = connections[using]
    conn.ensure_connection()
    db_settings = conn.settings_dict
    url = (
        f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}@"
        f"{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
    )
    return create_engine(url)


def django_model_fields_get(model_class, include_properties=True) -> list[str]:
    """Returns fields from Django model matching certain criteria
    to help us:
     - construct dropdowns in Airflow UI (ex: select clustering fields)
     - pick some fields we want to construct dataframes

    Always excluded: internals & ManyToMany
    """
    from django.db import models
    from django.utils.functional import cached_property

    # Internal Django fields retrieved when inspecting model
    # but we don't want to keep
    excluded = ["pk"]

    if not issubclass(model_class, models.Model):
        raise ValueError("The provided class must be a subclass of models.Model.")

    fields = [
        x.name
        for x in model_class._meta.get_fields()
        # ManyToMany case causing massive performance issues (e.g. on "sources")
        # and would require a different approach, maybe working via prepared
        # views
        if not isinstance(x, models.ManyToManyField)
    ]

    attributes = []
    if include_properties:
        for attr_name in dir(model_class):
            attr = getattr(model_class, attr_name, None)
            if isinstance(attr, property) or isinstance(attr, cached_property):
                attributes.append(attr_name)

    results = fields + attributes
    return [x for x in results if x not in excluded]


def django_model_queryset_generate(
    model_class,
    fields_include_all_filled: list[str],
    fields_exclude_any_filled: list[str],
):
    """Génère une requête Django à partir d'une liste de champs
    et de filtres pour un modèle donné.

    Utile pour des tâches Airflow qui doivent récupérer des données
    de la DB pour les traiter."""

    from django.db.models import Q

    # Pour faciliter l'utilisation de cette fonction on
    # exclude automatiquement les champs qui ne sont pas dans la
    # DB (ex: @property)
    db_fields = {f.name for f in model_class._meta.get_fields()}

    include_fields = [
        field for field in fields_include_all_filled if field in db_fields
    ]
    exclude_fields = [
        field for field in fields_exclude_any_filled if field in db_fields
    ]
    # select_fields = [field for field in fields_to_select if field in db_fields]

    # Inclure uniquement si TOUS les champs sont remplis
    include_all_filled_filter = Q()
    for field in include_fields:
        include_all_filled_filter &= ~Q(**{f"{field}": ""})

    # Exclure si N'IMPORTE QUEL champ est rempli
    # note: ce champ étant la négation de l'inclusion, on le construit
    # comme l'incusion et on fait une négation d'ensemble ensuite
    exclude_any_filled_filter = Q()
    for field in exclude_fields:
        exclude_any_filled_filter &= ~Q(**{f"{field}": ""})
    exclude_any_filled_filter = ~exclude_any_filled_filter

    final_filter = include_all_filled_filter & exclude_any_filled_filter

    return model_class.objects.filter(final_filter)


def django_model_queryset_to_sql(query: Any) -> str:
    """Fonction pour obtenir la requête SQL d'une query Django"""
    return str(query.query)


def django_model_to_pandas_schema(model_class: Any) -> dict[str, str]:
    """Génère un schema compatible avec pandas' dtype quand on construit
    une dataframe pour éviter que pandas ne fasse des inférences de type
    et ne vienne tout casser (ex: code_postal casté en float et qui créé
    bcp de bruit quand on renormalise en string: 53000 -> 53000.0 -> "53000.0")
    """
    # TODO: support pour des types complexes du genre
    # django.contrib.gis.db.models.fields.PointField pour lesquels
    # on devra peut être utiliser des libraries genre https://geopandas.org/en/stable/
    from django.db import models

    dtype_mapping = {
        models.AutoField: "int64",
        models.IntegerField: "int64",
        models.FloatField: "float64",
        models.DecimalField: "float64",
        models.BooleanField: "bool",
        models.CharField: "object",
        models.TextField: "object",
        models.DateField: "datetime64[ns]",
        models.DateTimeField: "datetime64[ns]",
        models.TimeField: "object",
        models.EmailField: "object",
        models.URLField: "object",
        models.UUIDField: "object",
        models.BinaryField: "object",
        models.ForeignKey: "int64",
    }

    schema = {}
    for field in model_class._meta.get_fields():
        if isinstance(field, models.Field):
            # Par défaut tout ce qui n'est pas trouvé
            # est attribué le type "object" (chaine de caractères)
            schema[field.name] = dtype_mapping.get(type(field), "object")  # type: ignore

    return schema


def django_model_queryset_to_df(query: Any, fields: list[str]) -> pd.DataFrame:
    """Converts a Django QuerySet into a dataframe"""
    fn = "django_model_queryset_to_df"
    log.preview(f"{fn}: query", django_model_queryset_to_sql(query))
    """
    # To make function more reliable we always exclude fields not
    # present in DB
    fields_in_db = django_model_fields_get(query.model, include_properties=False)
    fields_used = [x for x in fields if x in fields_in_db]

    data = list(query.values(*fields_used))
    """
    fields = list(set(fields))
    data = []
    # Reason we have to go for a loop and can't do list(query.values(*fields))
    # is because some of the fields are calculated props and don't exist in DB
    for n, entry in enumerate(query):
        data.append({field: getattr(entry, field) for field in fields})
        if n % 100 == 0:
            logger.info(f"{fn}: {n} entrées récupérées")
    log.preview(f"{fn}: entrées retournées", data)
    # dtype=object => don't try to infer type
    return pd.DataFrame(data, dtype=object)


def django_schema_create_and_check(schema_name: str, sql: str, dry_run=True) -> None:
    """Create a table in the DB from a schema"""
    from django.db import connection

    # Creation
    logger.info(f"Création schema pour {schema_name=}: début")
    log.preview("Schema", sql)
    if dry_run:
        logger.info("Mode dry-run, on ne crée pas le schema")
        return
    with connection.cursor() as cursor:
        cursor.execute(sql)

    # Validation
    tables_all = connection.introspection.table_names()
    if schema_name not in tables_all:
        raise SystemError(f"Table pas crée malgré execution SQL OK: {schema_name}")
    logger.info(f"Création schema pour {schema_name=}: succès 🟢")


def get_model_fields(model, with_relationships=True, latlong=False):
    fields = []
    for field in model._meta.get_fields():
        if field.is_relation and not with_relationships:
            continue
        if field.one_to_many or field.many_to_many:
            fields.append(field.name.rstrip("s") + "_codes")
        elif field.many_to_one:
            fields.append(field.name + "_code")
        else:
            fields.append(field.name)
    if latlong:
        fields.extend(["latitude", "longitude"])
        if "location" in fields:
            fields.remove("location")
    return fields

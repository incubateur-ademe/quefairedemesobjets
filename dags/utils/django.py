"""Utilitaires pour utiliser notre environement Django
dans Airflow.

⚠️ ATTENTION ⚠️ Pour que ceci fonctionne, il faut que
le code django de la repo soit disponible sur le serveur
qui fait tourner Airflow (ce qui est le cas au 2025-01-08)
ET que les dossiers core/ et qfdmo/ etc... soient montés dans
l'environement de Airflow si on passe par docker

Pour itérer en dev plus rapidement sur la conception/test
des fonctions d'initialisation django:

 - lancer le docker airflow
 - executer la commande ci-dessous qui affichera les
    problèmes de chargement des dags si il y en a

    docker exec -it qfdmo-airflow-scheduler-1 airflow dags list-import-errors

    🟢 Si aucune erreur la commande retourne: "No data found"
    🟠 Si il y a des erreurs, elles seront affichées
"""

import os
import sys
from pathlib import Path

import django
import pandas as pd
from django.conf import settings
from django.db import models
from django.db.models import Model, Q, QuerySet
from django.utils.functional import cached_property
from rich import print
from shared.tasks.database_logic.db_manager import PostgresConnectionManager


def django_add_to_sys_path() -> None:
    """Fonction qui ajoute la racine de notre projet Django à sys.path"""
    # On ajoute le dossier de 2 niveaux au dessus de celui du script
    # pour pouvoir importer le settings.py
    # Arborecence actuelle:
    # - core/
    # - dags/utils/django.py

    # Premier des 3x .parent sert à récupérer le dossier,
    # les 2 autres à remonter à la source de notre repo
    path_2_levels_up = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, path_2_levels_up)


def django_setup_full() -> None:
    """Initialisation complète de l'environement Django pour pouvoir,
    entre autres, importer et utiliser les modèles dans Airflow.

    Pour que l'init complète marche il faut que:
    - les dépendences django (python, lib systèmes) soit installées sur Airflow
    - les dossiers core/, qfdmo/ etc.. soient montés sur Airflow

    Voir airflow-scheduler.Dockerfile pour plus de détails"""
    django_add_to_sys_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()


def django_setup_partial() -> None:
    """Une initialisation partielle de l'environement Django

    ⚠️ A ne pas utiliser par défaut (prendre django_setup_full)
    mais à conserver au cas où un jour django_setup_full devient une
    usine à gaz et qu'on ait besoin d'une version plus légère."""
    import dj_database_url

    django_add_to_sys_path()
    db_url = str(PostgresConnectionManager().engine.url)
    default_settings = dj_database_url.parse(db_url)
    default_settings["ENGINE"] = "django.contrib.gis.db.backends.postgis"
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["qfdmo"],
            DATABASES={"default": default_settings},
        )
    django.setup()


def django_model_fields_attributes_get(model_class) -> list[str]:
    """Retournes les noms des champs et des attributs
    d'un modèle Django, par exemple pour offrir via
    la UI Airflow des dropdowns de champs à sélectionner
    pour des tâches de cluster."""

    if not issubclass(model_class, models.Model):
        raise ValueError("The provided class must be a subclass of models.Model.")

    fields = [field.name for field in model_class._meta.get_fields()]

    attributes = []
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name, None)
        if isinstance(attr, property) or isinstance(attr, cached_property):
            attributes.append(attr_name)

    return fields + attributes


def django_model_queryset_generate(
    model_class: type[Model],
    fields_include_all_filled: list[str],
    fields_exclude_any_filled: list[str],
    # fields_to_select: list[str],
) -> QuerySet:
    """Génère une requête Django à partir d'une liste de champs
    et de filtres pour un modèle donné.

    Utile pour des tâches Airflow qui doivent récupérer des données
    de la DB pour les traiter."""
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

    # Inclure uniquement si TOUS les champs qui sont tous remplis
    include_all_filled_filter = Q()
    for field in include_fields:
        include_all_filled_filter &= ~Q(**{f"{field}__isnull": True})

    # Exclude si N'IMPORTE QUEL champ est rempli
    exclude_any_filled_filter = Q()
    for field in exclude_fields:
        exclude_any_filled_filter &= ~Q(**{f"{field}__isnull": True})

    # Combine filters
    final_filter = include_all_filled_filter & ~exclude_any_filled_filter

    return model_class.objects.filter(final_filter)


def django_model_queryset_to_sql(query: QuerySet) -> str:
    """Fonction pour obtenir la requête SQL d'un QuerySet Django"""
    return str(query.query)


def django_model_to_pandas_schema(model_class: type[Model]) -> dict[str, str]:
    """Génère un schema compatible avec pandas' dtype quand on construit
    une dataframe pour éviter que pandas ne fasse des inférences de type
    et ne vienne tout casser (ex: code_postal casté en float et qui créé
    bcp de bruit quand on renormalise en string: 53000 -> 53000.0 -> "53000.0")"""
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
        # TODO: support pour des types complexes du genre
        # django.contrib.gis.db.models.fields.PointField pour lesquels
        # on devra peut être utiliser des libraries genre https://geopandas.org/en/stable/
    }

    schema = {}
    for field in model_class._meta.get_fields():
        if isinstance(field, models.Field):
            # Par défaut tout ce qui n'est pas trouvé
            # est attribué le type "object" (chaine de caractères)
            schema[field.name] = dtype_mapping.get(type(field), "object")  # type: ignore

    return schema


def django_model_queryset_to_df(query: QuerySet, fields: list[str]) -> pd.DataFrame:
    """Fonction pour obtenir un DataFrame Pandas à partir d'un QuerySet Django
    et de son modèle pour imposer un schema"""
    data = []
    sql = django_model_queryset_to_sql(query)
    print("sql", sql)
    for entry in query:
        data.append({field: getattr(entry, field) for field in set(fields)})
    if not data:
        raise ValueError("Pas de données retournées par la query.")

    # TODO: imposer le schema pour éviter les inférences de type
    # Pour l'instant on met dtype=object ce qui désactive l'inférence
    # et donc on consèrve les valeurs telles que fournies par Django
    # ce qui devrait suffire
    # dtype = django_model_to_pandas_schema(query.model)
    return pd.DataFrame(data, dtype=object)

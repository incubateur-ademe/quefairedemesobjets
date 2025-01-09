"""Utilitaires pour utiliser notre environement Django
dans Airflow.

⚠️ ATTENTION ⚠️ Pour que ceci fonctionne, il faut que
le code django de la repo soit disponible sur le serveur
qui fait tourner Airflow (ce qui est le cas au 2025-01-08)
ET que les dossiers core/ et qfdmo/ soient montés dans
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

import dj_database_url
import django
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
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

    Voir airflow-scheduler.Dockerfile pour plus de détails
    """
    django_add_to_sys_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    # 🔴 Crash car il manque les variables d'environement de .env
    # Quand on commence à jouer avec le .env ça devient compliqué
    django.setup()


def django_setup_partial() -> None:
    """Une initialisation partielle de l'environement Django

    ⚠️ A ne pas utiliser par défaut (prendre django_setup_full)
    mais à conserver au cas où un jour django_setup_full devient une
    usine à gaz et qu'on ait besoin d'une version plus légère
    """

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
    pour des tâches de clustering."""

    if not issubclass(model_class, models.Model):
        raise ValueError("The provided class must be a subclass of models.Model.")

    fields = [field.name for field in model_class._meta.get_fields()]

    attributes = []
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name, None)
        if isinstance(attr, property) or isinstance(attr, cached_property):
            attributes.append(attr_name)

    return fields + attributes

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

    # Preimer des 3x .parent sert à récupérer le dossier,
    # les 2 autres à remonter à la source de notre repo
    path_2_levels_up = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, path_2_levels_up)


def django_setup_full() -> None:
    """Initialisation de l'environement Django pour pouvoir,
    entre autres, importer et utiliser les modèles dans Airflow.

    FIXME: la loqigue d'ajout du path et le déclenchement de django.setup()
    marchent en soit, 🔴 mais on se retrouve bloquer par
    les variables d'environements

    On consèrve cette pour référence le jour où on cherche à essayer
    de faire le setup complet de Django dans Airflow
    """
    django_add_to_sys_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    # 🔴 Crash car il manque les variables d'environement de .env
    # Quand on commence à jouer avec le .env ça devient compliqué
    django.setup()


def django_setup_partial() -> None:
    """Une initialisation partielle de l'environement Django
    mais qui fonctionne pour ce qui est du chargement des modèles

    TODO: pour que cette fonction marche j'ai du rajouter app_label
    à tous nos modèles conformément au comportement de
    https://docs.djangoproject.com/en/5.1/ref/models/options/#django.db.models.Options.app_label
    "If a model is defined outside of an application in INSTALLED_APPS,
    it must declare which app it belongs to:"

    Ceci pourrait être amélioré en:
    - réussissant à définir app_label via settings.configure (j'ai pas trouvé)

    OU

    - définissant un modèle de base dont tous nos modèles héritent
    - définissant _meta.app_label = "qfdmo" uniquement sur ce modèle de base
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


def django_model_fields_attributes_get(model_class):
    if not issubclass(model_class, models.Model):
        raise ValueError("The provided class must be a subclass of models.Model.")

    # Get all field names
    fields = [field.name for field in model_class._meta.get_fields()]

    # Get all @property and @cached_property attributes
    attributes = []
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name, None)
        if isinstance(attr, property) or isinstance(attr, cached_property):
            attributes.append(attr_name)

    return fields + attributes

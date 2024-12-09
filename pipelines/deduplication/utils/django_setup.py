"""
Pour pouvoir utiliser les modèles Django au lieux de requêtes SQL mano

FIXME: définir une fonction d'initialisation qui prend un environnement,
pour l'instant on ne controle pas l'environnement de travail qui est
par défaut sur PREPROD

FIXME: aussi, cette méthode semble instantier Sentry alors que, voir:
https://www.notion.so/accelerateur-transition-ecologique-ademe/Sentry-gestion-pour-l-environement-de-dev-local-1536523d57d7807183b5ee811a7e4187?pvs=4
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

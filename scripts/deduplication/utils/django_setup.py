"""Pour pouvoir importer des modules Django dans notre script
il faut d'abord initialiser l'environnement Django
avec les settings"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

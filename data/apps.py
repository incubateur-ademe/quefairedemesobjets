from django.apps import AppConfig


class DataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data"
    label = "data"
    verbose_name = "Gestion des interactions avec la plateforme de données"

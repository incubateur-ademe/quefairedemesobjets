from django.apps import AppConfig


class DataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "data"
    label = "data"
    verbose_name = "Changements de données"

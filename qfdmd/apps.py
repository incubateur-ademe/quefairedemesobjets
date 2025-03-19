from django.apps import AppConfig


class QfdmoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # The space at the start of the name is intended, it forces
    # the app to appears on first position in django admin menu
    verbose_name = " 🚮 Assistant"
    name = "qfdmd"

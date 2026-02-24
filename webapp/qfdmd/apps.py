from django.apps import AppConfig


class QfdmoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # The space at the start of the name is intended, it forces
    # the app to appears on first position in django admin menu
    verbose_name = " 🚮 Assistant"
    name = "qfdmd"

    def ready(self):
        # The import here is required for signals to be executed during Django
        # initialization. These raise a flake8 warning but this is intended.
        # See https://docs.djangoproject.com/fr/5.2/topics/signals/
        # flake8: noqa: F401
        import qfdmd.signals

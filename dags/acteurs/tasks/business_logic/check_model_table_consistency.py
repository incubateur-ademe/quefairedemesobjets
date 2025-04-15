from utils.django import django_setup_full

django_setup_full()


def check_model_table_consistency(*, model_name: str, table_name: str) -> bool:

    from django.apps import apps

    from core.models.tools import compare_model_vs_table

    model_class = apps.get_model("qfdmo", model_name)
    return compare_model_vs_table(model_class, table_name)

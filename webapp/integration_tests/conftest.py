import pytest
from django.core.management import call_command
from django.db.models.signals import post_save
from modelsearch import index
from modelsearch.signal_handlers import post_save_signal_handler


def index_unless_loading_a_fixture(instance, raw=False, **kwargs):
    if not raw:
        post_save_signal_handler(instance, **kwargs)


@pytest.fixture(scope="session", autouse=True)
def skip_search_index_of_fixtures():
    """Indexing takes 13 ms per row, a minute for the synonymes fixture."""
    for model in index.get_indexed_models():
        if post_save.disconnect(post_save_signal_handler, sender=model):
            post_save.connect(index_unless_loading_a_fixture, sender=model)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "actions")

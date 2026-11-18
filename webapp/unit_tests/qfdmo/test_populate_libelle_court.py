import pytest
from django.core.management import call_command

from qfdmo.models.action import GroupeAction
from unit_tests.qfdmo.action_factory import GroupeActionFactory

pytestmark = pytest.mark.django_db


def test_sets_the_short_label_of_known_gestes():
    GroupeActionFactory(code="reparer", libelle_court="")
    GroupeActionFactory(code="autre", libelle_court="")

    call_command("populate_libelle_court")

    assert GroupeAction.objects.get(code="reparer").libelle_court == "Réparer"
    assert GroupeAction.objects.get(code="autre").libelle_court == ""


def test_is_idempotent():
    GroupeActionFactory(code="trier", libelle_court="")

    call_command("populate_libelle_court")
    call_command("populate_libelle_court")

    assert GroupeAction.objects.get(code="trier").libelle_court == "Déposer"

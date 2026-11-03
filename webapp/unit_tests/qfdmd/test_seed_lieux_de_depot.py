import pytest
from django.core.management import call_command

from qfdmd.management.commands.seed_lieux_de_depot import LIEUX
from qfdmd.models import LieuDeDepot

pytestmark = pytest.mark.django_db


def test_creates_every_lieu():
    LieuDeDepot.objects.all().delete()

    call_command("seed_lieux_de_depot")

    assert LieuDeDepot.objects.count() == len(LIEUX)


def test_leaves_an_edited_lieu_untouched():
    LieuDeDepot.objects.filter(code="bac_de_tri").update(libelle="Bac jaune")

    call_command("seed_lieux_de_depot")

    assert LieuDeDepot.objects.get(code="bac_de_tri").libelle == "Bac jaune"
    assert LieuDeDepot.objects.filter(code="bac_de_tri").count() == 1

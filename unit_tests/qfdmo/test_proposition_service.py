import pytest
from django.contrib.gis.geos import Point

from qfdmo.models import (
    ActeurService,
    Action,
    CategorieObjet,
    EconomieCirculaireActeur,
    PropositionService,
    SousCategorieObjet,
)


class TestActionNomAsNaturalKeyHeritage:
    @pytest.mark.django_db
    def test_serialize(self):
        acteur_service = ActeurService.objects.create(nom="Test Object", lvao_id=123)
        action = Action.objects.create(nom="Test Object", lvao_id=123)
        economie_circulaire_acteur = EconomieCirculaireActeur.objects.create(
            nom="Test Object", location=Point(0, 0)
        )
        proposition_service = PropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            economie_circulaire_acteur=economie_circulaire_acteur,
        )
        categorie = CategorieObjet.objects.create(nom="Test Category")
        sous_categorie1 = SousCategorieObjet.objects.create(
            nom="Test Sous-Categorie 1", categorie=categorie, lvao_id=123, code="C1"
        )
        sous_categorie2 = SousCategorieObjet.objects.create(
            nom="Test Sous-Categorie 2", categorie=categorie, lvao_id=123, code="C2"
        )
        proposition_service.sous_categories.add(sous_categorie1, sous_categorie2)

        assert proposition_service.serialize() == {
            "action": action.serialize(),
            "acteur_service": acteur_service.serialize(),
            "sous_categories": [
                sous_categorie1.serialize(),
                sous_categorie2.serialize(),
            ],
        }

import pytest
from django.contrib.gis.geos import Point

from qfdmo.models import (
    Acteur,
    ActeurService,
    Action,
    CategorieObjet,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
    SousCategorieObjet,
)


class TestActionNomAsNaturalKeyHeritage:
    @pytest.fixture
    def acteur_service(self):
        return ActeurService.objects.create(nom="fake acteur service", lvao_id=123)

    @pytest.fixture
    def action(self):
        return Action.objects.create(nom="fake action", lvao_id=123)

    @pytest.fixture
    def acteur(self):
        return Acteur.objects.create(
            nom="fake acteur",
            location=Point(0, 0),
            identifiant_unique="1",
            acteur_type_id=1,
        )

    @pytest.fixture
    def categorie(self):
        return CategorieObjet.objects.create(nom="fake categorie")

    @pytest.fixture
    def sous_categories(self, categorie):
        sous_categorie1 = SousCategorieObjet.objects.create(
            nom="fake sous-categorie 1", categorie=categorie, lvao_id=123, code="C1"
        )
        sous_categorie2 = SousCategorieObjet.objects.create(
            nom="fake sous-categorie 2", categorie=categorie, lvao_id=123, code="C2"
        )
        return [sous_categorie1, sous_categorie2]

    @pytest.fixture
    def proposition_service(self, acteur_service, action, acteur, sous_categories):
        proposition_service = PropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            acteur=acteur,
        )
        proposition_service.sous_categories.add(sous_categories[0], sous_categories[1])
        return proposition_service

    @pytest.fixture
    def revision_acteur(self):
        return RevisionActeur.objects.create(
            nom="fake revision acteur",
            location=Point(0, 0),
            identifiant_unique="1",
            acteur_type_id=1,
        )

    @pytest.fixture
    def revision_proposition_service(
        self, acteur_service, action, revision_acteur, sous_categories
    ):
        revision_proposition_service = RevisionPropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            acteur=revision_acteur,
        )
        revision_proposition_service.sous_categories.add(
            sous_categories[0], sous_categories[1]
        )
        return revision_proposition_service

    @pytest.mark.django_db
    def test_serialize(
        self, proposition_service, acteur_service, action, sous_categories, acteur
    ):
        assert proposition_service.serialize() == {
            "action": action.serialize(),
            "acteur_service": acteur_service.serialize(),
            "sous_categories": [
                sous_categories[0].serialize(),
                sous_categories[1].serialize(),
            ],
        }

    @pytest.mark.django_db
    def test_proposition_service_str(self, proposition_service):
        assert str(proposition_service) == (
            "fake acteur - fake action - fake acteur service"
        )

    @pytest.mark.django_db
    def test_revision_proposition_service_str(self, revision_proposition_service):
        assert str(revision_proposition_service) == (
            "fake revision acteur - fake action - fake acteur service"
        )

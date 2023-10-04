import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    Action,
    FinalActeur,
    NomAsNaturalKeyModel,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
)


class TestNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in Acteur.mro()


class TestPoint:
    def test_longitude_Latitude(self):
        acteur = Acteur(location=Point(1.1, 2.2))
        assert acteur.longitude == 1.1
        assert acteur.latitude == 2.2


class TestSerialize:
    @pytest.mark.django_db
    def test_serialize(self):
        acteur_type = ActeurType.objects.create(nom="Test Object", lvao_id=123)
        acteur = Acteur.objects.create(
            nom="Test Object", location=Point(0, 0), acteur_type=acteur_type
        )
        acteur_service = ActeurService.objects.create(nom="Test Object", lvao_id=123)
        action = Action.objects.create(nom="Test Object", lvao_id=123)
        proposition_service = PropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            acteur=acteur,
        )
        assert acteur.serialize() == {
            "id": acteur.id,
            "nom": "Test Object",
            "identifiant_unique": None,
            "acteur_type": acteur_type.serialize(),
            "adresse": None,
            "adresse_complement": None,
            "code_postal": None,
            "ville": None,
            "url": None,
            "email": None,
            "telephone": None,
            "multi_base": False,
            "nom_commercial": None,
            "nom_officiel": None,
            "manuel": False,
            "label_reparacteur": False,
            "siret": None,
            "source_donnee": None,
            "identifiant_externe": None,
            "location": {"type": "Point", "coordinates": [0.0, 0.0]},
            "proposition_services": [proposition_service.serialize()],
        }


@pytest.fixture(scope="session")
def populate_admin_object(django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "action_directions",
            "actions",
            "acteur_services",
            "acteur_types",
        )


@pytest.fixture()
def new_acteur(db, populate_admin_object):
    acteur_type = ActeurType.objects.first()
    acteur = Acteur.objects.create(
        nom="Test Object 1", location=Point(0, 0), acteur_type=acteur_type
    )
    acteur_service = ActeurService.objects.first()
    action = Action.objects.first()
    PropositionService.objects.create(
        acteur_service=acteur_service,
        action=action,
        acteur=acteur,
    )
    yield acteur


@pytest.mark.django_db
class TestActeurGetOrCreateRevisionActeur:
    def test_create_revisionacteur_copy1(self, populate_admin_object, new_acteur):
        revision_acteur = new_acteur.get_or_create_revision()

        assert revision_acteur.serialize() == new_acteur.serialize()

    def test_create_revisionacteur_copy2(self, populate_admin_object, new_acteur):
        revision_acteur = new_acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        revision_acteur2 = new_acteur.get_or_create_revision()

        assert revision_acteur2.serialize() == revision_acteur.serialize()
        assert revision_acteur2.nom == "Test Object 2"
        assert revision_acteur2.nom != new_acteur.nom

    def test_create_revisionacteur(self, populate_admin_object, new_acteur):
        revision_acteur = new_acteur.get_or_create_revision()
        acteur_service = ActeurService.objects.last()
        action = Action.objects.last()
        proposition_service = RevisionPropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            revision_acteur=revision_acteur,
        )
        revision_acteur.proposition_services.add(proposition_service)
        revision_acteur2 = new_acteur.get_or_create_revision()

        assert revision_acteur2.serialize() == revision_acteur.serialize()
        assert revision_acteur2.nom == new_acteur.nom
        assert (
            revision_acteur2.proposition_services.all()
            != new_acteur.proposition_services.all()
        )


@pytest.mark.django_db
class TestActeurMaterializedView:
    def test_materialized_view_empty(self, new_acteur):
        assert FinalActeur.objects.count() == 0

    def test_materialized_view_with_acteur(self, new_acteur):
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.first()
        serialized_final_acteur = final_acteur.serialize()
        serialized_final_acteur.pop("actions")

        assert FinalActeur.objects.count() == 1
        assert serialized_final_acteur == new_acteur.serialize()

    def test_materialized_view_with_acteur_even_if_revision(self, new_acteur):
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.first()

        revision_acteur = new_acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        final_acteur.refresh_from_db()
        serialized_final_acteur = final_acteur.serialize()
        serialized_final_acteur.pop("actions")

        assert serialized_final_acteur == new_acteur.serialize()
        assert serialized_final_acteur != revision_acteur.serialize()

    def test_materialized_view_with_revisionacteur(self, new_acteur):
        revision_acteur = new_acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.first()
        serialized_final_acteur = final_acteur.serialize()
        serialized_final_acteur.pop("actions")

        assert serialized_final_acteur == revision_acteur.serialize()
        assert serialized_final_acteur != new_acteur.serialize()


@pytest.mark.django_db
class TestCreateRevisionActeur:
    def test_new_revision_acteur(self, populate_admin_object):
        revision_acteur = RevisionActeur.objects.create(
            nom="Test Object 1",
            location=Point(0, 0),
            acteur_type=ActeurType.objects.first(),
        )
        assert revision_acteur.serialize() == Acteur.objects.first().serialize()


@pytest.mark.django_db
class TestFinalActeurActions:
    @pytest.fixture()
    def final_acteur_with_ps(db, populate_admin_object):
        action1 = Action.objects.get(nom="reparer")
        action2 = Action.objects.get(nom="echanger")
        action3 = Action.objects.get(nom="louer")
        acteur_service = ActeurService.objects.first()
        acteur = Acteur.objects.create(nom="Acteur 1", location=Point(0, 0))
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action1
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action2
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action3
        )
        FinalActeur.refresh_view()
        final_acteur_with_ps = FinalActeur.objects.get(id=acteur.id)
        yield final_acteur_with_ps

    def test_acteur_actions_basic(self, final_acteur_with_ps):
        actions = final_acteur_with_ps.acteur_actions()
        assert [action.nom for action in actions] == ["reparer", "echanger", "louer"]

    def test_acteur_actions_with_direction(self, final_acteur_with_ps):
        actions = final_acteur_with_ps.acteur_actions(direction="jai")
        assert [action.nom for action in actions] == ["reparer", "echanger"]

    def test_acteur_actions_order(self, final_acteur_with_ps):
        Action.objects.filter(nom="reparer").update(order=3)
        Action.objects.filter(nom="echanger").update(order=2)
        Action.objects.filter(nom="louer").update(order=1)
        actions = final_acteur_with_ps.acteur_actions()
        assert [action.nom for action in actions] == ["louer", "echanger", "reparer"]

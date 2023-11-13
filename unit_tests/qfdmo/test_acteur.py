import pytest
from django.contrib.gis.geos import Point
from django.core.management import call_command
from django.forms import ValidationError

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
    Source,
)
from qfdmo.models.action import CachedDirectionAction


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
        CachedDirectionAction.reload_cache()


@pytest.fixture()
def acteur(db, populate_admin_object):
    source = Source.objects.create(nom="Equipe")
    acteur_type = ActeurType.objects.first()
    acteur = Acteur.objects.create(
        nom="Test Object 1",
        location=Point(0, 0),
        acteur_type=acteur_type,
        identifiant_unique="1",
        identifiant_externe="456",
        acteur_type_id=1,
        source=source,
    )
    acteur_service = ActeurService.objects.first()
    action = Action.objects.first()
    PropositionService.objects.create(
        acteur_service=acteur_service,
        action=action,
        acteur=acteur,
    )
    yield acteur


@pytest.fixture()
def finalacteur(db, populate_admin_object):
    source = Source.objects.create(nom="Equipe")
    action1 = Action.objects.get(nom="reparer")
    action2 = Action.objects.get(nom="echanger")
    action3 = Action.objects.get(nom="louer")
    acteur_service = ActeurService.objects.first()
    acteur = Acteur.objects.create(
        nom="Acteur 1",
        location=Point(0, 0),
        identifiant_unique="1",
        acteur_type_id=1,
        source=source,
    )
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
    finalacteur = FinalActeur.objects.get(identifiant_unique=acteur.identifiant_unique)
    yield finalacteur


class TestNomAsNaturalKeyHeritage:
    def test_natural(self):
        assert NomAsNaturalKeyModel in Acteur.mro()


class TestPoint:
    def test_longitude_Latitude(self):
        acteur = Acteur(location=Point(1.1, 2.2))
        assert acteur.longitude == 1.1
        assert acteur.latitude == 2.2


class TestActeurNomAffiche:
    def test_nom(self):
        assert (
            Acteur(nom="Test Object 1", location=Point(0, 0)).nom_affiche
            == "Test Object 1"
        )

    def test_nom_commercial(self):
        assert (
            Acteur(
                nom="Test Object 1",
                location=Point(0, 0),
                nom_commercial="Nom commercial",
            ).nom_affiche
            == "Nom commercial"
        )


@pytest.mark.django_db
class TestActeurIsdigital:
    def test_isdigital_false(self, populate_admin_object):
        acteur_type = ActeurType.objects.exclude(nom="acteur digital").first()
        assert not Acteur(
            nom="Test Object 1", location=Point(0, 0), acteur_type=acteur_type
        ).is_digital

    def test_isdigital_true(self, populate_admin_object):
        acteur_type = ActeurType.objects.get(nom="acteur digital")
        assert Acteur(
            nom="Test Object 1", location=Point(0, 0), acteur_type=acteur_type
        ).is_digital


@pytest.mark.django_db
class TestActeurSerialize:
    def test_serialize(self, acteur):
        proposition_service = PropositionService.objects.last()
        expected_serialized_acteur = {
            "nom": "Test Object 1",
            "identifiant_unique": "1",
            "acteur_type": acteur.acteur_type.serialize(),
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
            "source": acteur.source.serialize(),
            "statut": "ACTIF",
            "identifiant_externe": "456",
            "location": {"type": "Point", "coordinates": [0.0, 0.0]},
            "naf_principal": None,
            "commentaires": None,
            "proposition_services": [proposition_service.serialize()],
        }
        assert acteur.serialize() == expected_serialized_acteur


@pytest.mark.django_db
class TestActeurDefaultOnSave:
    def test_empty(self):
        acteur = Acteur.objects.create(
            nom="Test Object 1",
            acteur_type_id=1,
            location=Point(0, 0),
        )
        assert len(acteur.identifiant_externe) == 12
        assert acteur.identifiant_unique == "equipe_" + acteur.identifiant_externe
        assert acteur.source.nom == "equipe"

    def test_default_identifiantunique(self):
        source = Source.objects.get_or_create(nom="Source")[0]
        acteur = Acteur.objects.create(
            nom="Test Object 1",
            acteur_type_id=1,
            location=Point(0, 0),
            source=source,
            identifiant_externe="123ABC",
        )
        assert acteur.identifiant_unique == "source_123ABC"

    def test_set_identifiantunique(self):
        acteur = Acteur.objects.create(
            nom="Test Object 1",
            acteur_type_id=1,
            location=Point(0, 0),
            identifiant_unique="Unique",
        )
        assert acteur.identifiant_unique == "Unique"


@pytest.mark.django_db
class TestLocationValidation:
    def test_location_validation_raise(self):
        acteur_type = ActeurType.objects.exclude(nom="acteur digital").first()
        acteur = Acteur(
            nom="Test Object 1", identifiant_unique="123", acteur_type=acteur_type
        )
        with pytest.raises(ValidationError):
            acteur.save()

    def test_location_validation_dont_raise(self):
        acteur_type = ActeurType.objects.get(nom="acteur digital")
        acteur = Acteur(
            nom="Test Object 1", identifiant_unique="123", acteur_type=acteur_type
        )
        acteur.save()
        assert acteur.identifiant_unique
        assert acteur.location is None


@pytest.mark.django_db
class TestActeurGetOrCreateRevisionActeur:
    def test_create_revisionacteur_copy1(self, populate_admin_object, acteur):
        revision_acteur = acteur.get_or_create_revision()

        assert (
            revision_acteur.serialize()["identifiant_unique"]
            == acteur.serialize()["identifiant_unique"]
        )

    def test_create_revisionacteur_copy2(self, populate_admin_object, acteur):
        revision_acteur = acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        revision_acteur2 = acteur.get_or_create_revision()

        assert revision_acteur2.serialize() == revision_acteur.serialize()
        assert revision_acteur2.nom == "Test Object 2"
        assert revision_acteur2.nom != acteur.nom

    def test_create_revisionacteur(self, populate_admin_object, acteur):
        revision_acteur = acteur.get_or_create_revision()
        acteur_service = ActeurService.objects.last()
        action = Action.objects.last()
        proposition_service = RevisionPropositionService.objects.create(
            acteur_service=acteur_service,
            action=action,
            revision_acteur=revision_acteur,
        )
        revision_acteur.proposition_services.add(proposition_service)
        revision_acteur2 = acteur.get_or_create_revision()

        assert revision_acteur2.serialize() == revision_acteur.serialize()
        assert revision_acteur2.nom is None
        assert (
            revision_acteur2.proposition_services.all()
            != acteur.proposition_services.all()
        )


@pytest.mark.django_db
class TestActeurMaterializedView:
    def test_materialized_view_empty(self, acteur):
        assert FinalActeur.objects.count() == 0

    def test_materialized_view_with_acteur(self, acteur):
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.first()
        serialized_final_acteur = final_acteur.serialize()
        serialized_final_acteur.pop("actions")

        assert FinalActeur.objects.count() == 1
        assert serialized_final_acteur == acteur.serialize()

    def test_materialized_view_with_acteur_even_if_revision(self, acteur):
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.first()

        revision_acteur = acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        final_acteur.refresh_from_db()
        serialized_final_acteur = final_acteur.serialize()
        serialized_final_acteur.pop("actions")

        assert serialized_final_acteur == acteur.serialize()
        assert serialized_final_acteur != revision_acteur.serialize()

    def test_materialized_view_with_revisionacteur(self, acteur):
        revision_acteur = acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.identifiant_externe = "789"
        revision_acteur.save()
        FinalActeur.refresh_view()
        final_acteur = FinalActeur.objects.get(
            identifiant_unique=acteur.identifiant_unique
        )

        assert final_acteur.nom == revision_acteur.nom
        assert final_acteur.nom != acteur.nom
        assert final_acteur.identifiant_externe == revision_acteur.identifiant_externe
        assert final_acteur.identifiant_externe != acteur.identifiant_externe
        assert final_acteur.source != revision_acteur.source
        assert final_acteur.source == acteur.source


@pytest.mark.django_db
class TestCreateRevisionActeur:
    def test_new_revision_acteur(self, populate_admin_object):
        revision_acteur = RevisionActeur.objects.create(
            nom="Test Object 1",
            location=Point(0, 0),
            acteur_type=ActeurType.objects.first(),
            acteur_type_id=1,
        )
        acteur = Acteur.objects.get(
            identifiant_unique=revision_acteur.identifiant_unique
        )
        assert revision_acteur.source == acteur.source
        assert revision_acteur.acteur_type == acteur.acteur_type


@pytest.mark.django_db
class TestFinalActeurSerialize:
    def test_finalacteur_serialize_basic(self, finalacteur):
        assert finalacteur.serialize() == {
            "nom": "Acteur 1",
            "identifiant_unique": "1",
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
            "source": finalacteur.source.serialize(),
            "statut": "ACTIF",
            "identifiant_externe": finalacteur.identifiant_externe,
            "location": {"type": "Point", "coordinates": [0.0, 0.0]},
            "naf_principal": None,
            "commentaires": None,
            "proposition_services": [
                proposition_service.serialize()
                for proposition_service in finalacteur.proposition_services.all()
            ],
            "actions": finalacteur.acteur_actions(),
            "acteur_type": finalacteur.acteur_type.serialize(),
        }

    def test_finalacteur_serialize_render_as_card(self, finalacteur):
        assert finalacteur.serialize(render_as_card=True) == {
            "nom": "Acteur 1",
            "identifiant_unique": "1",
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
            "source": finalacteur.source.serialize(),
            "statut": "ACTIF",
            "identifiant_externe": finalacteur.identifiant_externe,
            "location": {"type": "Point", "coordinates": [0.0, 0.0]},
            "naf_principal": None,
            "commentaires": None,
            "proposition_services": [
                proposition_service.serialize()
                for proposition_service in finalacteur.proposition_services.all()
            ],
            "actions": finalacteur.acteur_actions(),
            "acteur_type": finalacteur.acteur_type.serialize(),
            "render_as_card": finalacteur.render_as_card(),
        }

    def test_finalacteur_serialize_render_as_card_with_direction(self, finalacteur):
        assert finalacteur.serialize(render_as_card=True, direction="jai") == {
            "nom": "Acteur 1",
            "identifiant_unique": "1",
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
            "source": finalacteur.source.serialize(),
            "statut": "ACTIF",
            "identifiant_externe": finalacteur.identifiant_externe,
            "location": {"type": "Point", "coordinates": [0.0, 0.0]},
            "naf_principal": None,
            "commentaires": None,
            "proposition_services": [
                proposition_service.serialize()
                for proposition_service in finalacteur.proposition_services.all()
            ],
            "actions": finalacteur.acteur_actions(direction="jai"),
            "acteur_type": finalacteur.acteur_type.serialize(),
            "render_as_card": finalacteur.render_as_card(direction="jai"),
        }


@pytest.mark.django_db
class TestFinalActeurRenderascard:
    def test_finalacteur_renderascard_basic(self, finalacteur):
        finalacteur.adresse = "77 Av Segur"
        finalacteur.code_postal = "75007"
        finalacteur.ville = "Paris"

        html = finalacteur.render_as_card()

        for action in finalacteur.acteur_actions():
            assert action["nom_affiche"] in html
        for acteur_service in finalacteur.acteur_services():
            assert str(acteur_service) in html

        assert finalacteur.nom_affiche in html
        assert finalacteur.adresse in html
        assert finalacteur.code_postal in html
        assert finalacteur.ville in html
        assert "None" not in html

    def test_finalacteur_renderascard_detailed(self, finalacteur):
        finalacteur.adresse = "77 Av Segur"
        finalacteur.adresse_complement = "Dinum"
        finalacteur.code_postal = "75007"
        finalacteur.ville = "Paris"
        finalacteur.telephone = "01 02 03 04 05"
        finalacteur.url = "quefairedemesobjets.ademe.fr"

        html = finalacteur.render_as_card()

        assert finalacteur.adresse_complement in html
        assert finalacteur.telephone in html
        assert f'href="{finalacteur.url}"' in html
        assert "None" not in html


@pytest.mark.django_db
class TestFinalActeurActions:
    def test_acteur_actions_basic(self, finalacteur):
        actions = finalacteur.acteur_actions()
        assert [action["nom"] for action in actions] == ["reparer", "echanger", "louer"]

    def test_acteur_actions_with_direction(self, finalacteur):
        actions = finalacteur.acteur_actions(direction="jai")
        assert [action["nom"] for action in actions] == ["reparer", "echanger"]

    def test_acteur_actions_order(self, finalacteur):
        CachedDirectionAction.reload_cache()
        Action.objects.filter(nom="reparer").update(order=3)
        Action.objects.filter(nom="echanger").update(order=2)
        Action.objects.filter(nom="louer").update(order=1)
        actions = finalacteur.acteur_actions()
        assert [action["nom"] for action in actions] == ["louer", "echanger", "reparer"]


@pytest.mark.django_db
class TestActeurService:
    def test_acteur_actions_basic(self):
        action1 = Action.objects.get(nom="reparer")
        acteur_service = ActeurService.objects.get(
            nom="Achat, revente par un professionnel"
        )
        acteur = Acteur.objects.create(
            nom="Acteur 1", location=Point(0, 0), acteur_type_id=1
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action1
        )

        services = acteur.acteur_services()
        assert [str(service) for service in services] == [
            "Achat, revente par un professionnel"
        ]

    def test_acteur_actions_distinct(self):
        action1 = Action.objects.get(nom="reparer")
        acteur_service = ActeurService.objects.get(
            nom="Achat, revente par un professionnel"
        )
        action2 = Action.objects.get(nom="echanger")
        acteur = Acteur.objects.create(
            nom="Acteur 1",
            location=Point(0, 0),
            acteur_type_id=1,
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action1
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service, action=action2
        )

        services = acteur.acteur_services()
        assert [str(service) for service in services] == [
            "Achat, revente par un professionnel"
        ]

    def test_acteur_actions_multiple(self):
        action = Action.objects.get(nom="reparer")
        acteur_service1 = ActeurService.objects.get(
            nom="Achat, revente par un professionnel"
        )
        acteur_service2 = ActeurService.objects.get(nom="Atelier d'auto-réparation")
        acteur = Acteur.objects.create(
            nom="Acteur 1", location=Point(0, 0), acteur_type_id=1
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service1, action=action
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service2, action=action
        )

        services = acteur.acteur_services()
        assert [str(service) for service in services] == [
            "Achat, revente par un professionnel",
            "Atelier d'auto-réparation",
        ]

    def test_acteur_actions_multiple_with_same_nom_affiche(self):
        action = Action.objects.get(nom="reparer")
        acteur_service1 = ActeurService.objects.get(
            nom="Achat, revente par un professionnel"
        )
        acteur_service2 = ActeurService.objects.get(nom="Atelier d'auto-réparation")
        acteur_service2.nom_affiche = acteur_service1.nom_affiche
        acteur_service2.save()
        acteur = Acteur.objects.create(
            nom="Acteur 1", location=Point(0, 0), acteur_type_id=1
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service1, action=action
        )
        PropositionService.objects.create(
            acteur=acteur, acteur_service=acteur_service2, action=action
        )

        services = acteur.acteur_services()
        assert [str(service) for service in services] == [
            "Achat, revente par un professionnel",
        ]

import json

import pytest
from django.contrib.gis.geos import Point
from django.forms import ValidationError, model_to_dict
from factory import Faker

from qfdmo.models import (
    Acteur,
    NomAsNaturalKeyModel,
    RevisionActeur,
    RevisionPropositionService,
)
from qfdmo.models.acteur import DisplayedActeur, LabelQualite, Source
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurServiceFactory,
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
    PropositionServiceFactory,
    RevisionActeurFactory,
    RevisionPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import (
    ActionDirectionFactory,
    ActionFactory,
    GroupeActionFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture()
def acteur(db):
    ps = PropositionServiceFactory.create()
    yield ps.acteur


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
            Acteur(nom="Test Object 1", location=Point(1, 1)).libelle == "Test Object 1"
        )

    def test_nom_commercial(self):
        assert (
            Acteur(
                nom="Test Object 1",
                location=Point(1, 1),
                nom_commercial="Nom commercial",
            ).libelle
            == "Nom commercial"
        )


@pytest.mark.django_db
class TestActeurIsdigital:
    def test_isdigital_false(self):
        acteur_type = ActeurTypeFactory()
        assert not Acteur(
            nom="Test Object 1", location=Point(1, 1), acteur_type=acteur_type
        ).is_digital

    def test_isdigital_true(self):
        acteur_type = ActeurTypeFactory(code="acteur_digital")
        assert ActeurFactory.build(
            nom="Test Object 1", acteur_type=acteur_type
        ).is_digital

    def test_isdigital_hides_address(self):
        acteur_type = ActeurTypeFactory(code="acteur_digital")
        acteur = DisplayedActeurFactory(acteur_type=acteur_type)
        assert acteur.is_digital
        assert not acteur.should_display_adresse


@pytest.mark.django_db
class TestActeurDefaultOnSave:
    def test_empty(self):
        SourceFactory(code="Communauté Longue Vie Aux Objets")
        acteur_type = ActeurTypeFactory(code="fake")
        acteur = ActeurFactory(
            nom="Test Object 1",
            acteur_type_id=acteur_type.id,
            location=Point(1, 1),
            source=None,
        )
        assert len(acteur.identifiant_externe) == 12
        assert (
            acteur.identifiant_unique
            == "communaute_longue_vie_aux_objets_" + acteur.identifiant_externe
        )
        assert acteur.source.code == "Communauté Longue Vie Aux Objets"

    def test_default_identifiantunique(self):
        source = SourceFactory(code="source_equipe")
        acteur_type = ActeurTypeFactory(code="fake")

        acteur = ActeurFactory(
            nom="Test Object 1",
            acteur_type_id=acteur_type.id,
            location=Point(1, 1),
            source=source,
            identifiant_externe="123ABC",
        )
        assert acteur.identifiant_unique == "source_equipe_123ABC"

    def test_set_identifiantunique(self):
        acteur_type = ActeurTypeFactory(code="fake")
        acteur = ActeurFactory(
            nom="Test Object 1",
            acteur_type_id=acteur_type.id,
            location=Point(1, 1),
            identifiant_unique="Unique",
        )
        assert acteur.identifiant_unique == "Unique"


@pytest.mark.django_db
class TestActeurOpeningHours:
    def test_horaires_ok(self):
        acteur_type = ActeurTypeFactory(code="fake")
        acteur = Acteur(
            nom="Test Object 1",
            acteur_type_id=acteur_type.id,
            location=Point(1, 1),
        )
        assert acteur.full_clean() is None
        acteur.horaires = ""
        assert acteur.full_clean() is None
        acteur.horaires = "24/7"
        assert acteur.full_clean() is None
        acteur.horaires = "Mo-Fr 09:00-12:00,13:00-18:00; Sa 09:00-12:00"
        assert acteur.full_clean() is None

    def test_horaires_ko(self):
        acteur = Acteur(
            nom="Test Object 1",
            location=Point(1, 1),
        )
        acteur.horaires_osm = "24/24"
        with pytest.raises(ValidationError):
            acteur.full_clean()


@pytest.mark.django_db
class TestActeurLocationValidation:
    def test_location_validation_raise(self):
        acteur_type = ActeurTypeFactory()
        acteur = Acteur(
            nom="Test Object 1", identifiant_unique="123", acteur_type=acteur_type
        )
        with pytest.raises(ValidationError):
            acteur.save()

    def test_location_validation_dont_raise(self):
        acteur_type = ActeurTypeFactory(code="acteur_digital")
        acteur = Acteur(
            nom="Test Object 1", identifiant_unique="123", acteur_type=acteur_type
        )
        acteur.save()
        assert acteur.identifiant_unique
        assert acteur.location is None


@pytest.mark.django_db
class TestActeurGetOrCreateRevisionActeur:
    def test_create_revisionacteur_copy1(self, acteur):
        revision_acteur = acteur.get_or_create_revision()

        assert revision_acteur.identifiant_unique == acteur.identifiant_unique

    def test_create_revisionacteur_copy2(self, acteur):
        revision_acteur = acteur.get_or_create_revision()
        revision_acteur.nom = "Test Object 2"
        revision_acteur.save()
        revision_acteur2 = acteur.get_or_create_revision()

        assert revision_acteur2 == revision_acteur
        assert revision_acteur2.nom == "Test Object 2"
        assert revision_acteur2.nom != acteur.nom

    def test_create_revisionacteur(self, acteur):
        revision_acteur = acteur.get_or_create_revision()
        revision_acteur.proposition_services.all().delete()
        action = ActionFactory.create(code="action 2")
        proposition_service = RevisionPropositionService.objects.create(
            action=action,
            acteur=revision_acteur,
        )
        revision_acteur.proposition_services.add(proposition_service)
        revision_acteur2 = acteur.get_or_create_revision()

        assert revision_acteur2 == revision_acteur
        assert revision_acteur2.nom is None
        assert (
            revision_acteur2.proposition_services.values_list("action__code").all()
            != acteur.proposition_services.values_list("action__code").all()
        )


@pytest.mark.django_db
class TestCreateRevisionActeur:
    def test_new_revision_acteur(self):
        acteur_type = ActeurTypeFactory(code="fake")
        revision_acteur = RevisionActeur.objects.create(
            nom="Test Object 1",
            location=Point(1, 1),
            acteur_type=acteur_type,
        )
        acteur = Acteur.objects.get(
            identifiant_unique=revision_acteur.identifiant_unique
        )
        assert revision_acteur.source == acteur.source
        assert revision_acteur.acteur_type == acteur.acteur_type

    def test_new_revision_acteur_with_action_principale(self):
        acteur_type = ActeurTypeFactory(code="fake")
        action_principale = ActionFactory(code="action 1")
        revision_acteur = RevisionActeur.objects.create(
            nom="Test Object 1",
            location=Point(1, 1),
            acteur_type=acteur_type,
            action_principale=action_principale,
        )
        acteur = Acteur.objects.get(
            identifiant_unique=revision_acteur.identifiant_unique
        )
        assert revision_acteur.action_principale == acteur.action_principale

    def test_new_revision_acteur_on_acteur_with_proposition_services(self):
        acteur = ActeurFactory()
        proposition_service = PropositionServiceFactory()
        acteur.proposition_services.add(proposition_service)
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        assert acteur.proposition_services.count() > 0
        assert revision_acteur.proposition_services.count() > 0

    def test_revision_acteur_is_parent(self):
        revision_acteur_parent = RevisionActeurFactory()
        revision_acteur = RevisionActeurFactory(parent=revision_acteur_parent)

        assert revision_acteur_parent.is_parent
        assert not revision_acteur.is_parent

    def test_revision_acteur_parent_validator(self):
        revision_acteur_parent = RevisionActeurFactory()
        revision_acteur = RevisionActeurFactory(parent=revision_acteur_parent)

        with pytest.raises(ValidationError):
            RevisionActeurFactory(parent=revision_acteur)


@pytest.mark.django_db
class TestCreateRevisionActeurCreateParent:
    def test_create_parent_from_acteur(self):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique,
            nom=None,
            location=None,
            acteur_type=None,
        )

        revision_acteur_parent = revision_acteur.create_parent()

        assert revision_acteur_parent.nom == acteur.nom
        assert revision_acteur_parent.acteur_type == acteur.acteur_type
        assert revision_acteur_parent.location == acteur.location

        assert revision_acteur_parent.nom != revision_acteur.nom
        assert revision_acteur_parent.acteur_type != revision_acteur.acteur_type
        assert revision_acteur_parent.location != revision_acteur.location

    def test_create_parent_from_revision_acteur(self):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )

        revision_acteur_parent = revision_acteur.create_parent()

        assert revision_acteur_parent.nom != acteur.nom
        assert revision_acteur_parent.acteur_type != acteur.acteur_type
        assert revision_acteur_parent.location != acteur.location

        assert revision_acteur_parent.nom == revision_acteur.nom
        assert revision_acteur_parent.acteur_type == revision_acteur.acteur_type
        assert revision_acteur_parent.location == revision_acteur.location

    def test_create_parent_source(self):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )

        revision_acteur_parent = revision_acteur.create_parent()
        assert revision_acteur_parent.source is None

    def test_create_parent_labels(self):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        labels = LabelQualiteFactory()
        acteur.labels.add(labels)
        revision_acteur.labels.add(labels)

        revision_acteur_parent = revision_acteur.create_parent()

        assert revision_acteur_parent.labels.count() == 0

    def test_create_parent_proposition_services(self):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        proposition_services = PropositionServiceFactory()
        acteur.proposition_services.add(proposition_services)
        revision_proposition_services = RevisionPropositionServiceFactory()
        revision_acteur.proposition_services.add(revision_proposition_services)

        revision_acteur_parent = revision_acteur.create_parent()

        assert revision_acteur_parent.proposition_services.count() == 0


@pytest.mark.django_db
class TestRevisionActeurDuplicate:
    def test_duplicate(self):
        acteur = ActeurFactory(nom_commercial="Nom commercial")
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique,
            nom_commercial=None,
            nom="Nom Revision",
        )
        revision_acteur_duplicate = revision_acteur.duplicate()

        assert (
            revision_acteur_duplicate.nom == "Nom Revision"
        ), f"Should be the name of the revision : {revision_acteur.nom}"
        assert (
            revision_acteur_duplicate.acteur_type == revision_acteur.acteur_type
        ), f"Should be the acteur type of the revision : {revision_acteur.acteur_type}"
        assert (
            revision_acteur_duplicate.location == revision_acteur.location
        ), f"Should be the location of the revision : {revision_acteur.location}"
        assert (
            revision_acteur_duplicate.nom_commercial == "Nom commercial"
        ), f"Should be the nom commercial of the acteur : {acteur.source}"

    def test_duplicate_source(self):
        SourceFactory(code="Communauté Longue Vie Aux Objets")
        revision_acteur = RevisionActeurFactory()
        revision_acteur_duplicate = revision_acteur.duplicate()

        assert revision_acteur_duplicate.source == Source.objects.get(
            code="Communauté Longue Vie Aux Objets"
        )

    def test_duplicate_labels(self):
        revision_acteur = RevisionActeurFactory()
        label1 = LabelQualiteFactory()
        label2 = LabelQualiteFactory()
        revision_acteur.labels.add(label1)
        revision_acteur.labels.add(label2)

        print(revision_acteur.labels.all())

        revision_acteur_duplicate = revision_acteur.duplicate()

        assert revision_acteur_duplicate.labels.count() == 2
        assert set(
            [label.code for label in revision_acteur_duplicate.labels.all()]
        ) == {
            label1.code,
            label2.code,
        }

    def test_duplicate_proposition_services(self):
        SourceFactory(code="Communauté Longue Vie Aux Objets")
        revision_acteur = RevisionActeurFactory()
        proposition_services1 = RevisionPropositionServiceFactory(
            acteur=revision_acteur, action=ActionFactory(code="action1")
        )
        proposition_services2 = RevisionPropositionServiceFactory(
            acteur=revision_acteur, action=ActionFactory(code="action2")
        )
        sous_categorie1 = SousCategorieObjetFactory()
        sous_categorie2 = SousCategorieObjetFactory()
        proposition_services1.sous_categories.add(sous_categorie1, sous_categorie2)
        proposition_services2.sous_categories.add(sous_categorie1)

        revision_acteur_duplicate = revision_acteur.duplicate()
        assert revision_acteur_duplicate.proposition_services.count() == 2
        assert set(
            [
                (ps.action.code, ps.sous_categories.count())
                for ps in revision_acteur_duplicate.proposition_services.all()
            ]
        ) == {("action1", 2), ("action2", 1)}


@pytest.mark.django_db
class TestActeurService:

    @pytest.fixture
    def displayed_acteur(self):
        return DisplayedActeurFactory()

    def test_acteur_actions_basic(self, displayed_acteur):
        displayed_acteur.acteur_services.add(
            ActeurServiceFactory(libelle="Par un professionnel")
        )

        assert displayed_acteur.sorted_acteur_services_libelles == [
            "Par un professionnel"
        ]

    def test_acteur_actions_multiple(self, displayed_acteur):
        displayed_acteur.acteur_services.add(
            ActeurServiceFactory(code="pro", libelle="Par un professionnel"),
            ActeurServiceFactory(
                code="atelier", libelle="Atelier pour réparer soi-même"
            ),
        )

        assert displayed_acteur.sorted_acteur_services_libelles == [
            "Atelier pour réparer soi-même",
            "Par un professionnel",
        ]


class TestActeurPropositionServicesByDirection:
    @pytest.mark.django_db
    def test_proposition_services_by_direction(self):
        acteur = ActeurFactory()
        direction_jai = ActionDirectionFactory(code="jai")
        action = ActionFactory()
        action.directions.add(direction_jai)
        proposition_service = PropositionServiceFactory(acteur=acteur, action=action)
        acteur.proposition_services.add(proposition_service)
        assert list(acteur.proposition_services_by_direction("jai")) == [
            proposition_service
        ]
        assert list(acteur.proposition_services_by_direction("jecherche")) == []


class TestActeurLabel:
    @pytest.mark.django_db
    def test_has_label_reparacteur(self):
        acteur = ActeurFactory()
        label, _ = LabelQualite.objects.get_or_create(code="reparacteur")
        acteur.labels.add(label)
        assert acteur.has_label_reparacteur()


@pytest.mark.django_db
class TestDisplayActeurActeurActions:

    def test_basic(self):
        displayed_acteur = DisplayedActeurFactory()
        direction = ActionDirectionFactory(code="jai")
        action = ActionFactory()
        action.directions.add(direction)
        DisplayedPropositionServiceFactory(action=action, acteur=displayed_acteur)
        assert [
            model_to_dict(a, exclude=["directions"])
            for a in displayed_acteur.acteur_actions()
        ] == [
            {
                "id": action.id,
                "code": "action",
                "libelle": "Action",
                "libelle_groupe": "",
                "afficher": True,
                "description": None,
                "order": action.order,
                "couleur": "#C3992A",
                "icon": None,
                "groupe_action": None,
            }
        ]

    def test_with_direction(self):
        displayed_acteur = DisplayedActeurFactory()
        direction = ActionDirectionFactory(code="jai")
        action = ActionFactory()
        action.directions.add(direction)
        DisplayedPropositionServiceFactory(action=action, acteur=displayed_acteur)
        assert displayed_acteur.acteur_actions(direction="fake") == []
        assert [
            model_to_dict(a, exclude=["directions"])
            for a in displayed_acteur.acteur_actions(direction="jai")
        ] == [
            {
                "id": action.id,
                "code": "action",
                "libelle": "Action",
                "libelle_groupe": "",
                "afficher": True,
                "description": None,
                "order": action.order,
                "couleur": "#C3992A",
                "icon": None,
                "groupe_action": None,
            }
        ]

    def test_ordered_action(self):
        displayed_acteur = DisplayedActeurFactory()
        direction = ActionDirectionFactory(code="jai")
        for i in [2, 1, 3]:
            action = ActionFactory(order=i, code=f"{i}")
            action.directions.add(direction)
            DisplayedPropositionServiceFactory(action=action, acteur=displayed_acteur)

        assert [
            action.order for action in displayed_acteur.acteur_actions(direction="jai")
        ] == [1, 2, 3]


@pytest.mark.django_db
class TestDisplayedActeurJsonActeurForDisplay:

    @pytest.fixture
    def displayed_acteur(self):
        displayed_acteur = DisplayedActeurFactory()
        directionjai = ActionDirectionFactory(code="jai")
        directionjecherche = ActionDirectionFactory(code="jecherche")
        groupeaction1order2 = GroupeActionFactory(
            code="groupe1",
            icon="icon-groupeaction1",
            couleur="couleur-groupeaction1",
            order=2,
        )
        groupeaction2order1 = GroupeActionFactory(
            code="groupe2",
            icon="icon-groupeaction2",
            couleur="couleur-groupeaction2",
            order=1,
        )
        action1 = ActionFactory(
            code="actionjai1",
            icon="icon-actionjai1",
            couleur="couleur-actionjai1",
            groupe_action=groupeaction1order2,
            order=1,
        )
        action1.directions.add(directionjai)
        action2 = ActionFactory(
            code="actionjai2",
            icon="icon-actionjai2",
            couleur="couleur-actionjai2",
            groupe_action=groupeaction2order1,
            order=2,
        )
        action2.directions.add(directionjai)
        action3 = ActionFactory(
            code="actionjecherche1",
            icon="icon-actionjecherche1",
            couleur="couleur-actionjecherche1",
            groupe_action=groupeaction1order2,
            order=3,
        )
        action3.directions.add(directionjecherche)
        action4 = ActionFactory(
            code="actionjecherche2",
            icon="icon-actionjecherche2",
            couleur="couleur-actionjecherche2",
            groupe_action=groupeaction2order1,
            order=4,
        )
        action4.directions.add(directionjecherche)

        DisplayedPropositionServiceFactory(action=action1, acteur=displayed_acteur)
        DisplayedPropositionServiceFactory(action=action2, acteur=displayed_acteur)
        DisplayedPropositionServiceFactory(action=action3, acteur=displayed_acteur)
        DisplayedPropositionServiceFactory(action=action4, acteur=displayed_acteur)

        return displayed_acteur

    def test_json_acteur_for_display_ordered(self, displayed_acteur):
        acteur_for_display = json.loads(displayed_acteur.json_acteur_for_display())

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai1"
        assert acteur_for_display["couleur"] == "couleur-actionjai1"

    def test_json_acteur_for_display_by_direction(self, displayed_acteur):
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(direction="jai")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai1"
        assert acteur_for_display["couleur"] == "couleur-actionjai1"

        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(direction="jecherche")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjecherche1"
        assert acteur_for_display["couleur"] == "couleur-actionjecherche1"

    def test_json_acteur_for_display_action_list(self, displayed_acteur):
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(action_list="actionjai2")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai2"
        assert acteur_for_display["couleur"] == "couleur-actionjai2"

        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(
                action_list="actionjai1|actionjai2|actionjecherche2"
            )
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai1"
        assert acteur_for_display["couleur"] == "couleur-actionjai1"

    def test_json_acteur_for_display_carte(self, displayed_acteur):
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(carte=True)
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-groupeaction2"
        assert acteur_for_display["couleur"] == "couleur-groupeaction2"

    def test_json_acteur_for_display_carte_direction(self, displayed_acteur):
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(carte=True, direction="jecherche")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-groupeaction2"
        assert acteur_for_display["couleur"] == "couleur-groupeaction2"

    def test_json_acteur_for_display_carte_action_list(self, displayed_acteur):
        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(
                carte=True, action_list="actionjai1|actionjecherche1"
            )
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-groupeaction1"
        assert acteur_for_display["couleur"] == "couleur-groupeaction1"

        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(
                carte=True, action_list="actionjai1|actionjai2|actionjecherche2"
            )
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-groupeaction2"
        assert acteur_for_display["couleur"] == "couleur-groupeaction2"

    def test_json_acteur_for_display_action_principale_basic(self, displayed_acteur):
        displayed_acteur.action_principale = ActionFactory(code="actionjai2")
        displayed_acteur.save()

        acteur_for_display = json.loads(displayed_acteur.json_acteur_for_display())

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai2"
        assert acteur_for_display["couleur"] == "couleur-actionjai2"

    def test_json_acteur_for_display_action_principale_not_in_direction(
        self, displayed_acteur
    ):
        displayed_acteur.action_principale = ActionFactory(code="actionjai2")
        displayed_acteur.save()

        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(direction="jecherche")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjecherche1"
        assert acteur_for_display["couleur"] == "couleur-actionjecherche1"

    def test_json_acteur_for_display_action_principale_not_in_list(
        self, displayed_acteur
    ):
        displayed_acteur.action_principale = ActionFactory(code="actionjai2")
        displayed_acteur.save()

        acteur_for_display = json.loads(
            displayed_acteur.json_acteur_for_display(action_list="actionjai1")
        )

        assert acteur_for_display["uuid"] is not None
        assert acteur_for_display["location"] is not None
        assert acteur_for_display["icon"] == "icon-actionjai1"
        assert acteur_for_display["couleur"] == "couleur-actionjai1"


class TestDisplayedActeurDisplayPostalAddress:

    def test_should_display_adresse(self):
        displayed_acteur = DisplayedActeurFactory.build()

        assert displayed_acteur.should_display_adresse is False

    @pytest.mark.parametrize(
        "fields",
        [
            {"adresse": Faker("address")},
            {"adresse_complement": Faker("address")},
            {"code_postal": Faker("postalcode")},
            {"ville": Faker("city")},
        ],
    )
    def test_should_display_adresse_not_empty(self, fields):
        displayed_acteur = DisplayedActeurFactory.build(**fields)

        assert displayed_acteur.should_display_adresse is True


@pytest.mark.django_db
class TestActeurOrdering:
    def test_in_bbox_ordering_is_random(self):
        DisplayedActeurFactory.create_batch(20)
        bbox_whole_planet = [-180, -90, 180, 90]
        # in_bbox is explicitely called each time so that
        # the ordering of the queryset is re-computed.
        # We expect it to change at least once
        assert DisplayedActeur.objects.all().in_bbox(bbox_whole_planet).count() > 0
        first_acteur = DisplayedActeur.objects.all().in_bbox(bbox_whole_planet).first()
        while (
            first_acteur
            == DisplayedActeur.objects.all().in_bbox(bbox_whole_planet).first()
        ):
            first_acteur = (
                DisplayedActeur.objects.all().in_bbox(bbox_whole_planet).first()
            )

    def test_in_geojson_ordering_is_random(self):
        DisplayedActeurFactory.create_batch(20)
        geojson_whole_planet = json.dumps(
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-180, 90],
                            [180, 90],
                            [180, -90],
                            [-180, -90],
                            [-180, 90],
                        ]
                    ]
                ],
            }
        )
        # in_geojson is explicitely called each time so that
        # the ordering of the queryset is re-computed.
        # We expect it to change at least once
        assert (
            DisplayedActeur.objects.all().in_geojson(geojson_whole_planet).count() > 0
        )
        first_acteur = (
            DisplayedActeur.objects.all().in_geojson(geojson_whole_planet).first()
        )
        while (
            first_acteur
            == DisplayedActeur.objects.all().in_geojson(geojson_whole_planet).first()
        ):
            first_acteur = (
                DisplayedActeur.objects.all().in_geojson(geojson_whole_planet).first()
            )

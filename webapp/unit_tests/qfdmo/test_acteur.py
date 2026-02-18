import json
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point
from django.forms import ValidationError, model_to_dict
from factory.faker import Faker

from qfdmo.models import Acteur, RevisionActeur, RevisionPropositionService
from qfdmo.models.acteur import (
    ActeurReprise,
    ActeurStatus,
    DisplayedActeur,
    LabelQualite,
    Source,
    VueActeur,
)
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurServiceFactory,
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
    PerimetreADomicileFactory,
    PropositionServiceFactory,
    RevisionActeurFactory,
    RevisionPropositionServiceFactory,
    SourceFactory,
    VueActeurFactory,
)
from unit_tests.qfdmo.action_factory import ActionDirectionFactory, ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def acteur(db):
    ps = PropositionServiceFactory.create()
    yield ps.acteur


@pytest.fixture
def displayed_acteur(db):
    return DisplayedActeurFactory()


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
        SourceFactory(code="communautelvao")
        acteur_type = ActeurTypeFactory(code="fake")
        acteur = ActeurFactory(
            nom="Test Object 1",
            acteur_type_id=acteur_type.id,
            location=Point(1, 1),
            source=None,
        )
        assert len(acteur.identifiant_externe) == 12
        assert (
            acteur.identifiant_unique == "communautelvao_" + acteur.identifiant_externe
        )
        assert acteur.source.code == "communautelvao"

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
    @pytest.mark.parametrize(
        "horaires_osm",
        ["", "24/7", "Mo-Fr 09:00-12:00,13:00-18:00; Sa 09:00-12:00", "__empty__"],
    )
    def test_horaires_ok(self, horaires_osm):
        acteur = ActeurFactory(horaires_osm=horaires_osm)
        assert acteur.full_clean() is None

    def test_horaires_ko(self):
        acteur = ActeurFactory(horaires_osm="24/24")
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
        action = ActionFactory.create(code="action_2")
        proposition_service = RevisionPropositionService.objects.create(
            action=action,
            acteur=revision_acteur,
        )
        revision_acteur.proposition_services.add(proposition_service)
        revision_acteur2 = acteur.get_or_create_revision()

        assert revision_acteur2 == revision_acteur
        assert revision_acteur2.nom == ""
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

    def test_empty_email_acteur(self):
        acteur = ActeurFactory()
        acteur.email = "__empty__"
        with pytest.raises(ValidationError):
            acteur.full_clean()

    def test_empty_email_revision_acteur(self):
        revision_acteur = RevisionActeurFactory(email="__empty__")
        revision_acteur.email = "__empty__"
        assert revision_acteur.full_clean() is None

        acteur = Acteur.objects.get(
            identifiant_unique=revision_acteur.identifiant_unique
        )
        assert acteur.full_clean() is None

    def test_new_revision_acteur_with_action_principale(self):
        acteur_type = ActeurTypeFactory(code="fake")
        action_principale = ActionFactory(code="action_1")
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

    def test_create_revision_acteur_from_acteur_with_perimetre_adomiciles(self):
        acteur = ActeurFactory(lieu_prestation=Acteur.LieuPrestation.A_DOMICILE)
        acteur.perimetre_adomiciles.add(PerimetreADomicileFactory())
        revision_acteur = acteur.get_or_create_revision()
        assert (
            revision_acteur.lieu_prestation == Acteur.LieuPrestation.A_DOMICILE
        ), "le lieu de prestation est copié de Acteur"
        assert (
            revision_acteur.perimetre_adomiciles.count() == 1
        ), "Les perimètres adomiciles doivent être copiés"


@pytest.mark.django_db
class TestCreateRevisionActeurCreateParent:
    @pytest.fixture
    def acteurs_fields(self):
        acteur_type = ActeurTypeFactory()
        action_principale = ActionFactory()
        return {
            "nom": "Test Nom",
            "description": "Test Description",
            "acteur_type": acteur_type,
            "adresse": "123 rue Test",
            "adresse_complement": "Apt 4B",
            "code_postal": "75001",
            "ville": "Paris",
            "url": "https://test.com",
            "email": "test@test.com",
            "location": Point(2.349014, 48.864716),  # Paris
            "telephone": "0123456789",
            "nom_commercial": "Test Commercial",
            "nom_officiel": "Test Officiel",
            "siren": "123456789",
            "siret": "12345678901234",
            "identifiant_externe": "TEST123",
            "statut": "ACTIF",
            "naf_principal": "4791A",
            "commentaires": "Test Commentaires",
            "horaires_osm": "Mo-Fr 09:00-18:00",
            "horaires_description": "Ouvert en semaine",
            "public_accueilli": "Particuliers",
            "reprise": ActeurReprise.UN_POUR_UN,
            "exclusivite_de_reprisereparation": True,
            "uniquement_sur_rdv": True,
            "action_principale": action_principale,
        }

    def test_create_parent_from_revision_acteur(self, acteurs_fields):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            **acteurs_fields, identifiant_unique=acteur.identifiant_unique
        )

        # Create parent
        revision_acteur_parent = revision_acteur.create_parent()
        for field in set(acteurs_fields.keys()) - {"identifiant_externe"}:
            assert getattr(revision_acteur_parent, field) == getattr(
                revision_acteur, field
            )
            if field != "statut":
                assert getattr(revision_acteur_parent, field) != getattr(acteur, field)

        assert (
            revision_acteur_parent.identifiant_unique
            != revision_acteur.identifiant_unique
        )

        # reset values
        assert revision_acteur_parent.source is None
        assert revision_acteur_parent.identifiant_externe == ""

        # parent is not linked to any labels, services or proposition services
        assert revision_acteur_parent.labels.count() == 0
        assert revision_acteur_parent.acteur_services.count() == 0
        assert revision_acteur_parent.proposition_services.count() == 0

        # Parent is well set on child
        assert revision_acteur.parent == revision_acteur_parent

    def test_create_parent_from_acteur(self, acteurs_fields):
        acteur = ActeurFactory()
        del acteurs_fields["nom"]
        del acteurs_fields["location"]
        del acteurs_fields["acteur_type"]
        revision_acteur = RevisionActeurFactory(
            **acteurs_fields,
            identifiant_unique=acteur.identifiant_unique,
            nom="",
            location=None,
            acteur_type=None,
        )

        revision_acteur_parent = revision_acteur.create_parent()

        for field in set(acteurs_fields.keys()) - {
            "identifiant_externe",
        }:
            assert getattr(revision_acteur_parent, field) == getattr(
                revision_acteur, field
            )

        assert revision_acteur_parent.nom == acteur.nom
        assert revision_acteur_parent.acteur_type == acteur.acteur_type
        assert revision_acteur_parent.location == acteur.location

        assert revision_acteur_parent.nom != revision_acteur.nom
        assert revision_acteur_parent.acteur_type != revision_acteur.acteur_type
        assert revision_acteur_parent.location != revision_acteur.location

        # reset values
        assert revision_acteur_parent.source is None
        assert revision_acteur_parent.identifiant_externe == ""

        # parent is not linked to any labels, services or proposition services
        assert revision_acteur_parent.labels.count() == 0
        assert revision_acteur_parent.acteur_services.count() == 0
        assert revision_acteur_parent.proposition_services.count() == 0

        # Parent is well set on child
        assert revision_acteur.parent == revision_acteur_parent

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
        action = ActionFactory()
        acteur_type = ActeurTypeFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique,
            nom_commercial="",
            nom="Nom Revision",
            action_principale=action,
            acteur_type=acteur_type,
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
        SourceFactory(code="communautelvao")
        revision_acteur = RevisionActeurFactory()
        revision_acteur_duplicate = revision_acteur.duplicate()

        assert revision_acteur_duplicate.source == Source.objects.get(
            code="communautelvao"
        )

    def test_duplicate_labels(self):
        revision_acteur = RevisionActeurFactory()
        label1 = LabelQualiteFactory()
        label2 = LabelQualiteFactory()
        revision_acteur.labels.add(label1)
        revision_acteur.labels.add(label2)

        revision_acteur_duplicate = revision_acteur.duplicate()

        assert revision_acteur_duplicate.labels.count() == 2
        assert set(
            [label.code for label in revision_acteur_duplicate.labels.all()]
        ) == {label1.code, label2.code}

    def test_duplicate_proposition_services(self):
        SourceFactory(code="communautelvao")
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
class TestRevisionActeurRemoveParentWithoutChildren:
    def test_revision_acteur_remove_parent_without_children(self):
        revision_acteur_original_parent = RevisionActeurFactory()
        revision_acteur = RevisionActeurFactory(parent=revision_acteur_original_parent)

        assert RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Parent exists"

        revision_acteur_new_parent = RevisionActeurFactory()
        revision_acteur.parent = revision_acteur_new_parent
        revision_acteur.save()

        assert not RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Old parent is removed because it doesn't have any child"

    def test_revision_acteur_remove_parent_without_children2(self):
        revision_acteur_original_parent = RevisionActeurFactory()
        revision_acteur = RevisionActeurFactory(parent=revision_acteur_original_parent)

        assert RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Parent exists"

        revision_acteur.parent = None
        revision_acteur.save()

        assert not RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Old parent is removed because it doesn't have any child"

    def test_revision_acteur_dont_remove_parent_with_children(self):
        revision_acteur_original_parent = RevisionActeurFactory()
        revision_acteur1 = RevisionActeurFactory(parent=revision_acteur_original_parent)
        # Another child
        RevisionActeurFactory(parent=revision_acteur_original_parent)

        assert RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Parent exists"

        revision_acteur_new_parent = RevisionActeurFactory()
        revision_acteur1.parent = revision_acteur_new_parent
        revision_acteur1.save()

        assert RevisionActeur.objects.filter(
            pk=revision_acteur_original_parent.pk
        ).exists(), "Old parent isn't removed because it still have a child"


@pytest.mark.django_db
class TestActeurService:
    def test_acteur_services_basic(self, displayed_acteur):
        displayed_acteur.acteur_services.add(
            ActeurServiceFactory(libelle="Par un professionnel")
        )

        assert displayed_acteur.sorted_acteur_services_libelles == [
            "Par un professionnel"
        ]

    def test_acteur_services_multiple(self, displayed_acteur):
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


@pytest.mark.django_db
class TestActeurActions:
    @pytest.fixture
    def displayed_acteur(self):
        return DisplayedActeurFactory()

    def test_acteur_actions_filtered(self, displayed_acteur):
        direction_jai = ActionDirectionFactory(code="jai")
        action = ActionFactory(code="reparer")
        action.directions.add(direction_jai)
        DisplayedPropositionServiceFactory(acteur=displayed_acteur, action=action)

        assert len(displayed_acteur.acteur_actions()) == 1, (
            "ensure no filters on the action or direction"
            "generates a non-empty list of acteurs"
        )
        assert len(displayed_acteur.acteur_actions(direction="jai")) == 1, (
            "a filter with acteurs providing services for this action direct"
            "for this direction generates an empty list of acteurs",
        )
        assert len(displayed_acteur.acteur_actions(direction="jecherche")) == 0, (
            "a filter without acteurs providing services for this action direct"
            "for this direction generates an empty list of acteurs",
        )
        assert (
            len(displayed_acteur.acteur_actions(actions_codes="reparer|vendre")) == 1
        ), (
            "a filter with acteur providing services for this action code returns",
            "a non-empty list",
        )
        assert (
            len(displayed_acteur.acteur_actions(actions_codes="trier|vendre")) == 0
        ), (
            "a filter without acteurs providing services for this action code returns",
            "an empty list",
        )


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
        assert len(displayed_acteur.acteur_actions(direction="fake")) == 0
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


class TestDisplayedActeurFormUrls:
    def test_suggestion_form_url(self, displayed_acteur):
        displayed_acteur.nom = "Palais de l'Élysée"
        displayed_acteur.adresse = "55 rue du Faubourg Saint-Honoré"
        displayed_acteur.ville = "Paris"

        assert displayed_acteur.suggestion_form_url == (
            "/proposer-une-modification?Nom=Palais+de+l%27%C3%89lys%C3%A9e"
            "&Ville=Paris"
            "&Adresse=55+rue+du+Faubourg+Saint-Honor%C3%A9"
        )


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
class TestDisplayedActeurActionToDisplay:
    @pytest.mark.parametrize("actions", [None, []])
    def test_action_to_display_no_actions(self, actions):
        with patch(
            "qfdmo.models.acteur.DisplayedActeur.acteur_actions"
        ) as mock_acteur_actions:
            mock_acteur_actions.return_value = actions
            displayed_acteur = DisplayedActeurFactory()
            assert displayed_acteur.action_to_display() is None

    def test_action_to_display_actions(self):
        action1 = ActionFactory(code="action1", order=2)
        action2 = ActionFactory(code="action2", order=1)
        actions = [action1, action2]
        displayed_acteur = DisplayedActeurFactory()
        with patch(
            "qfdmo.models.acteur.DisplayedActeur.acteur_actions"
        ) as mock_acteur_actions:
            mock_acteur_actions.return_value = actions
            assert displayed_acteur.action_to_display() == action2

    def test_action_to_display_action_principale(self):
        action1 = ActionFactory(code="action1")
        action2 = ActionFactory(code="action2")
        action3 = ActionFactory(code="action3")
        actions = [action1, action2]
        displayed_acteur = DisplayedActeurFactory(action_principale=action3)
        with patch(
            "qfdmo.models.acteur.DisplayedActeur.acteur_actions"
        ) as mock_acteur_actions:
            mock_acteur_actions.return_value = actions
            assert displayed_acteur.action_to_display() == action1

        actions = [action2, action1, action3]
        with patch(
            "qfdmo.models.acteur.DisplayedActeur.acteur_actions"
        ) as mock_acteur_actions:
            mock_acteur_actions.return_value = actions
            assert displayed_acteur.action_to_display() == action3


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


@pytest.mark.django_db
class TestFinalActeurManagerGetActiveParents:
    @pytest.mark.parametrize(
        "factory,model",
        [(VueActeurFactory, VueActeur), (DisplayedActeurFactory, DisplayedActeur)],
    )
    def test_finalacteur_get_active_parents_returns_only_active_without_source(
        self, factory, model
    ):
        """Test that get_active_parents returns only active acteurs without source"""
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        # Active acteur without source - should be returned
        acteur_1 = factory(
            statut=ActeurStatus.ACTIF, source=None, acteur_type=acteur_type
        )
        acteur_2 = factory(
            statut=ActeurStatus.ACTIF, source=None, acteur_type=acteur_type
        )

        # Inactive acteur without source - should not be returned
        factory(statut=ActeurStatus.INACTIF, source=None, acteur_type=acteur_type)

        # Active acteur with source - should not be returned
        factory(statut=ActeurStatus.ACTIF, source=source, acteur_type=acteur_type)

        # Deleted acteur without source - should not be returned
        factory(statut=ActeurStatus.SUPPRIME, source=None, acteur_type=acteur_type)

        result = model.objects.get_active_parents()

        assert result.count() == 2
        assert acteur_1 in result
        assert acteur_2 in result

    @pytest.mark.parametrize(
        "factory,model",
        [(VueActeurFactory, VueActeur), (DisplayedActeurFactory, DisplayedActeur)],
    )
    def test_finalacteur_get_active_parents_empty_when_no_matching(
        self, factory, model
    ):
        """
        Test that get_active_parents returns an empty queryset
        when no actors match the criteria
        """
        acteur_type = ActeurTypeFactory()
        source = SourceFactory()

        # Create actors that do not match the criteria
        factory(statut=ActeurStatus.INACTIF, source=None, acteur_type=acteur_type)
        factory(statut=ActeurStatus.ACTIF, source=source, acteur_type=acteur_type)

        result = model.objects.get_active_parents()

        assert result.count() == 0

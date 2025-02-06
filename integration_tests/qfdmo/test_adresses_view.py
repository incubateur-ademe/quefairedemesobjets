import pytest
from django.contrib.gis.geos import Point
from django.http import HttpRequest
from django.test import override_settings

from qfdmo.leaflet import compile_leaflet_bbox
from qfdmo.models.acteur import ActeurStatus, DisplayedActeur
from qfdmo.views.adresses import CarteSearchActeursView
from unit_tests.core.test_utils import query_dict_from
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def action_reparer():
    action = ActionFactory(code="reparer")
    return action


@pytest.fixture
def action_preter():
    action = ActionFactory(code="preter")
    return action


@pytest.fixture
def action_donner():
    action = ActionFactory(code="donner")
    return action


@pytest.fixture
def sous_categorie():
    sous_categorie = SousCategorieObjetFactory()
    return sous_categorie


@pytest.fixture
def sous_categorie2():
    sous_categorie = SousCategorieObjetFactory()
    return sous_categorie


@pytest.fixture
def proposition_service_reparer(action_reparer, sous_categorie):
    proposition_service_reparer = DisplayedPropositionServiceFactory(
        action=action_reparer,
    )
    proposition_service_reparer.sous_categories.add(sous_categorie)
    return proposition_service_reparer


@pytest.fixture
def proposition_service_preter(action_preter, sous_categorie):
    proposition_service_preter = DisplayedPropositionServiceFactory(
        action=action_preter,
    )
    proposition_service_preter.sous_categories.add(sous_categorie)
    return proposition_service_preter


@pytest.fixture
def proposition_service_donner(action_donner, sous_categorie):
    proposition_service_donner = DisplayedPropositionServiceFactory(
        action=action_donner,
    )
    proposition_service_donner.sous_categories.add(sous_categorie)
    return proposition_service_donner


@pytest.fixture
def displayed_acteur_reparer(proposition_service_reparer):
    displayed_acteur = DisplayedActeurFactory(
        exclusivite_de_reprisereparation=True,
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    displayed_acteur.proposition_services.add(proposition_service_reparer)
    return displayed_acteur


@pytest.fixture
def displayed_acteur_reparacteur(displayed_acteur_reparer):

    reparacteur = LabelQualiteFactory(code="reparacteur")
    displayed_acteur_reparer.labels.add(reparacteur)
    return displayed_acteur_reparer


@pytest.fixture
def adresses_view():
    adresses_view = CarteSearchActeursView()
    return adresses_view


@pytest.fixture
def displayed_acteur_preter(proposition_service_preter):
    displayed_acteur_preter = DisplayedActeurFactory(
        nom="Un acteur preter",
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )

    displayed_acteur_preter.proposition_services.add(proposition_service_preter)
    return displayed_acteur_preter


@pytest.fixture
def displayed_acteur_donner(proposition_service_donner):
    displayed_acteur_donner = DisplayedActeurFactory(
        nom="Un acteur donner",
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    displayed_acteur_donner.proposition_services.add(proposition_service_donner)
    return displayed_acteur_donner


@pytest.fixture
def displayed_acteur_donner_sscat_preter_sscat2(
    sous_categorie, sous_categorie2, action_donner, action_preter
):
    displayed_acteur = DisplayedActeurFactory(
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )

    proposition_service_donner = DisplayedPropositionServiceFactory(
        action=action_donner,
    )
    proposition_service_donner.sous_categories.add(sous_categorie)

    proposition_service_preter = DisplayedPropositionServiceFactory(
        action=action_preter,
    )
    proposition_service_preter.sous_categories.add(sous_categorie2)

    displayed_acteur.proposition_services.add(proposition_service_donner)
    displayed_acteur.proposition_services.add(proposition_service_preter)

    return displayed_acteur


@pytest.fixture
def displayed_acteur_donner_reparer(
    proposition_service_donner, proposition_service_reparer
):
    displayed_acteur = DisplayedActeurFactory(
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    displayed_acteur.proposition_services.add(proposition_service_donner)
    displayed_acteur.proposition_services.add(proposition_service_reparer)

    return displayed_acteur


@pytest.mark.django_db
class TestReparacteur:
    def test_filtre_reparacteur_return_0_acteur(
        self, adresses_view, displayed_acteur_reparer, action_reparer
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "label_reparacteur": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_filtre_reparacteur_return_1_reparacteur(
        self, adresses_view, displayed_acteur_reparacteur, action_reparer
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "label_reparacteur": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1

    def test_filtre_reparacteur_return_1_noreparacteur(
        self,
        adresses_view,
        displayed_acteur_donner_reparer,
        action_reparer,
        action_donner,
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_donner.code}"],
                "latitude": [1],
                "longitude": [1],
                "label_reparacteur": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1


@pytest.mark.django_db
class TestReparerAlternateIcon:
    def test_no_action_reparer_selected_does_not_add_reparer_attribute(
        self, adresses_view, displayed_acteur_donner_reparer, action_donner
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_donner.code],
                "latitude": [1],
                "longitude": [1],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        with pytest.raises(AttributeError):
            context["acteurs"].first().reparer

    def test_action_reparer_selected_adds_reparer_attribute_on_actors_with_reparation(
        self,
        adresses_view,
        displayed_acteur_donner_reparer,
        action_donner,
        action_reparer,
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_donner.code, action_reparer.code],
                "latitude": [1],
                "longitude": [1],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()
        assert context["acteurs"].first().reparer


@pytest.mark.django_db
class TestExclusiviteReparation:
    def test_no_action_reparer_excludes_acteurs_avec_exclusivite(
        self, adresses_view, displayed_acteur_reparer, action_preter
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_preter.code],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_excludes_acteurs_avec_exclusivite_by_default(
        self, adresses_view, displayed_acteur_reparer, action_reparer, action_preter
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_preter.code}"],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 0

    def test_action_reparer_and_exclusivite_includes_acteurs_with_exclusivite(
        self, adresses_view, displayed_acteur_reparer, action_reparer
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1

    def test_sous_categorie_filter_works_with_exclu_reparation(
        self, adresses_view, displayed_acteur_reparer, sous_categorie, action_reparer
    ):
        request = HttpRequest()
        sous_categorie_id = sous_categorie.id
        request.GET = query_dict_from(
            {
                "action_list": [action_reparer.code],
                "latitude": [1],
                "longitude": [1],
                "sc_id": [str(sous_categorie_id)],
                "pas_exclusivite_reparation": ["false"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 1


@pytest.mark.django_db
class TestFilters:
    @pytest.mark.parametrize("carte", [[True], [None]])
    def test_action_filters(
        self,
        carte,
        adresses_view,
        action_reparer,
        action_preter,
        proposition_service_preter,
        proposition_service_donner,
        displayed_acteur_reparer,
        displayed_acteur_donner,
        displayed_acteur_preter,
        sous_categorie,
    ):
        proposition_service_preter.sous_categories.add(sous_categorie)
        proposition_service_donner.sous_categories.add(sous_categorie)

        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_preter.code}"],
                "latitude": [1],
                "longitude": [1],
                "sc_id": [sous_categorie.id],
                "carte": carte,
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert context["acteurs"].count() == 2

    def test_sous_categorie_filter(
        self,
        adresses_view,
        sous_categorie,
        displayed_acteur_reparer,
        displayed_acteur_donner,
        displayed_acteur_preter,
    ):
        request = HttpRequest()
        sous_categorie_id = sous_categorie.id
        request.GET = query_dict_from(
            {
                "latitude": [1],
                "longitude": [1],
                "sc_id": [str(sous_categorie_id)],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert DisplayedActeur.objects.count() > 1
        assert context["acteurs"].count() == 3

    def test_sous_categorie_filter_by_action_no_match(
        self,
        action_preter,
        sous_categorie,
        displayed_acteur_donner_sscat_preter_sscat2,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        sous_categorie_id = sous_categorie.id
        request.GET = query_dict_from(
            {
                "action_list": [action_preter.code],
                "latitude": [1],
                "longitude": [1],
                "sc_id": [str(sous_categorie_id)],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert DisplayedActeur.objects.count() > 1
        assert context["acteurs"].count() == 0

    def test_sous_categorie_filter_by_action_1_match(
        self,
        action_preter,
        sous_categorie2,
        displayed_acteur_donner_sscat_preter_sscat2,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        sous_categorie_id = sous_categorie2.id
        request.GET = query_dict_from(
            {
                "action_list": [action_preter.code],
                "latitude": [1],
                "longitude": [1],
                "sc_id": [str(sous_categorie_id)],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert DisplayedActeur.objects.count() > 1
        assert context["acteurs"].count() == 1


@pytest.mark.django_db
class TestBBOX:
    def test_bbox_is_returned_if_no_acteurs(self):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        leaflet_bbox = compile_leaflet_bbox([1, 1, 1, 1])
        request.GET = query_dict_from({})
        request.GET.update(bounding_box=leaflet_bbox)
        adresses_view.setup(request)

        acteurs = DisplayedActeur.objects.all()
        assert acteurs.count() == 0
        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox == leaflet_bbox

    @override_settings(DISTANCE_MAX=100000000000)
    def test_no_bbox_and_acteurs_from_center_if_no_acteurs_found_in_bbox(
        self,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        bbox = [0, 0, 0, 0]
        leaflet_bbox = compile_leaflet_bbox(bbox)
        request.GET = query_dict_from({})
        request.GET.update(bounding_box=leaflet_bbox, latitude="1", longitude="1")
        adresses_view.setup(request)

        DisplayedActeurFactory.create_batch(2)
        acteurs = DisplayedActeur.objects.all()
        assert acteurs.in_bbox(bbox).count() == 0
        assert acteurs.from_center(1, 1).count() == 2

        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox is None
        assert acteurs.count() == 2

    def test_bbox_and_acteurs_are_returned_if_contained_in_bbox(self):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        bbox = [-2, -2, 4, 4]  # Acteurs in factory are created with a location of 3, 3
        leaflet_bbox = compile_leaflet_bbox(bbox)
        request.GET = query_dict_from({})
        request.GET.update(bounding_box=leaflet_bbox, latitude="1", longitude="1")
        adresses_view.setup(request)

        DisplayedActeurFactory.create_batch(2)
        acteurs = DisplayedActeur.objects.all()
        assert acteurs.in_bbox(bbox).count() == 2

        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox == bbox
        assert acteurs.count() == 2


@pytest.mark.django_db
class TestLayers:
    def test_adresse_missing_layer_is_displayed(self, client):
        url = "/carte"
        response = client.get(url)
        assert 'data-testid="adresse-missing"' in str(response.content)

    def test_adresse_missing_layer_is_not_displayed_with_bbox(self, client):
        url = "/carte=1&direction=jai&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.916%2C%22lng%22%3A2.298202514648438%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.98742568330284%2C%22lng%22%3A2.483596801757813%7D%7D"  # noqa: E501
        response = client.get(url)
        assert 'data-testid="adresse-missing"' not in str(response.content)

    def test_adresse_missing_layer_is_not_displayed_for_epcis(self, client):
        url = "/carte?action_list=reparer%7Cdonner%7Cechanger%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre&epci_codes=200055887&limit=50"  # noqa: E501
        response = client.get(url)
        assert 'data-testid="adresse-missing"' not in str(response.content)

import pytest
from django.contrib.gis.geos import Point
from django.http import HttpRequest

from qfdmo.models.acteur import ActeurStatus, DisplayedActeur
from qfdmo.views.adresses import CarteView
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
    adresses_view = CarteView()
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
class TestExclusiviteReparation:
    def test_pas_action_reparer_exclut_acteurs_avec_exclusivite(
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

    def test_action_reparer_exclut_par_defaut_acteurs_avec_exclusivite(
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

    def test_action_reparer_et_exclusivite_inclut_acteurs_avec_exclusivite(
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
        adresses_view = CarteView()
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
        adresses_view = CarteView()
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

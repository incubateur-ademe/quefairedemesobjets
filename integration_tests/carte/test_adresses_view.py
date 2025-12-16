from urllib.parse import urlencode

import pytest
from django.contrib.gis.geos import Point
from django.http import HttpRequest
from django.test import RequestFactory, override_settings

from qfdmo.map_utils import compile_frontend_bbox
from qfdmo.models.acteur import (
    Acteur,
    ActeurStatus,
    DisplayedActeur,
    LabelQualite,
    RevisionActeur,
)
from qfdmo.views.carte import CarteSearchActeursView
from unit_tests.core.test_utils import query_dict_from
from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
    RevisionActeurFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


@pytest.fixture
def acteur_type_commerce():
    return ActeurTypeFactory(code="commerce")


@pytest.fixture
def action_reparer():
    groupe = GroupeActionFactory()
    action = ActionFactory(code="reparer", groupe_action=groupe)
    return action


@pytest.fixture
def action_preter():
    groupe = GroupeActionFactory()
    action = ActionFactory(code="preter", groupe_action=groupe)
    return action


@pytest.fixture
def action_donner():
    groupe = GroupeActionFactory()
    action = ActionFactory(code="donner", groupe_action=groupe)
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
    DisplayedActeur.objects.update(
        exclusivite_de_reprisereparation=False,
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    return DisplayedActeur.objects.first()


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
    DisplayedActeur.objects.update(
        nom="Un acteur preter",
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )

    return DisplayedActeur.objects.first()


@pytest.fixture
def displayed_acteur_donner(proposition_service_donner):
    DisplayedActeur.objects.update(
        nom="Un acteur donner",
        location=Point(1, 1),
        statut=ActeurStatus.ACTIF,
    )
    return DisplayedActeur.objects.first()


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


@pytest.fixture
def adresses_view_class():
    return CarteSearchActeursView


class RunViewMixin:
    def _run_view(self, rf, view_class, params):
        """Calls the CBV using its full lifecycle (dispatch/get/form_valid etc.).
        Returns `response` and `context`.
        """
        request = rf.get("/carte", params)
        response = view_class.as_view()(request)

        return response, getattr(response, "context_data", {})


@pytest.mark.django_db()
class TestReparacteur(RunViewMixin):
    @pytest.fixture
    def rf(self):
        return RequestFactory()

    def test_filtre_reparacteur_return_0_acteur(
        self, rf, adresses_view_class, displayed_acteur_reparer, action_reparer
    ):
        LabelQualiteFactory(code="reparacteur")
        params = {
            "action_list": [action_reparer.code],
            "map-latitude": 1,
            "map-longitude": 1,
            "label_reparacteur": "true",
        }

        response, context = self._run_view(rf, adresses_view_class, params)

        assert LabelQualite.objects.filter(code="reparacteur").exists()
        assert not DisplayedActeur.objects.filter(
            labels__code__in=["reparacteur"],
            proposition_services__action__code__in=["reparer"],
        ).exists()
        assert DisplayedActeur.objects.count() == 1
        assert response.status_code == 200
        assert len(context["acteurs"]) == 0

    def test_filtre_reparacteur_return_1_reparacteur(
        self, rf, adresses_view_class, displayed_acteur_reparacteur, action_reparer
    ):
        params = {
            "action_list": [action_reparer.code],
            "map-latitude": 1,
            "map-longitude": 1,
            "label_reparacteur": "true",
        }

        response, context = self._run_view(rf, adresses_view_class, params)

        assert response.status_code == 200
        assert len(context["acteurs"]) == 1

    def test_filtre_reparacteur_return_1_noreparacteur(
        self,
        rf,
        adresses_view_class,
        displayed_acteur_donner_reparer,
        action_reparer,
        action_donner,
    ):
        params = {
            "action_list": [f"{action_reparer.code}|{action_donner.code}"],
            "map-latitude": 1,
            "map-longitude": 1,
            "label_reparacteur": "true",
        }

        _, context = self._run_view(rf, adresses_view_class, params)

        assert len(context["acteurs"]) == 1


@pytest.mark.django_db
class TestReparerAlternateIcon(RunViewMixin):
    def test_no_action_reparer_selected_does_not_add_reparer_attribute(
        self, adresses_view, displayed_acteur_donner_reparer, action_donner
    ):
        request = HttpRequest()
        request.GET = query_dict_from(
            {
                "action_list": [action_donner.code],
                "map-latitude": [1],
                "map-longitude": [1],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        with pytest.raises(AttributeError):
            context["acteurs"].first().reparer

    def Z_test_action_reparer_selected_adds_reparer_attribute_on_actors_with_reparation(
        self,
        rf,
        adresses_view_class,
        displayed_acteur_donner_reparer,
        action_donner,
        action_reparer,
    ):
        params = {
            "action_list": [action_donner.code, action_reparer.code],
            "map-latitude": [1],
            "map-longitude": [1],
        }
        _, context = self._run_view(rf, adresses_view_class, params)

        assert context["acteurs"].first().reparer


@pytest.mark.django_db
class TestExclusiviteReparation(RunViewMixin):
    def test_no_action_reparer_excludes_acteurs_avec_exclusivite(
        self, rf, adresses_view_class, displayed_acteur_reparer, action_preter
    ):
        params = {
            "action_list": [action_preter.code],
            "map-latitude": [1],
            "map-longitude": [1],
            # This form is enabled by default
            # "pas_exclusivite_reparation": ["true"],
        }
        _, context = self._run_view(rf, adresses_view_class, params)
        assert len(context["acteurs"]) == 0

    def test_action_reparer_excludes_acteurs_avec_exclusivite_by_default(
        self, adresses_view, displayed_acteur_reparer, action_reparer, action_preter
    ):
        request = HttpRequest()
        DisplayedActeur.objects.update(exclusivite_de_reprisereparation=True)
        request.GET = query_dict_from(
            {
                "action_list": [f"{action_reparer.code}|{action_preter.code}"],
                "map-latitude": [1],
                "map-longitude": [1],
                "pas_exclusivite_reparation": ["true"],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert len(context["acteurs"]) == 0

    def test_action_reparer_and_exclusivite_includes_acteurs_with_exclusivite(
        self, rf, adresses_view_class, displayed_acteur_reparer, action_reparer
    ):
        DisplayedActeur.objects.update(exclusivite_de_reprisereparation=False)
        params = {
            "action_list": [action_reparer.code],
            "map-latitude": [1],
            "map-longitude": [1],
            "pas_exclusivite_reparation": ["false"],
        }
        _, context = self._run_view(rf, adresses_view_class, params)

        assert len(context["acteurs"]) == 1

    def test_sous_categorie_filter_works_with_exclu_reparation(
        self,
        rf,
        adresses_view_class,
        displayed_acteur_reparer,
        sous_categorie,
        action_reparer,
    ):
        sous_categorie_id = sous_categorie.id
        params = {
            "action_list": [action_reparer.code],
            "map-latitude": [1],
            "map-longitude": [1],
            "sc_id": [str(sous_categorie_id)],
            "pas_exclusivite_reparation": ["false"],
        }
        _, context = self._run_view(rf, adresses_view_class, params)

        assert len(context["acteurs"]) == 1


@pytest.mark.django_db
class TestFilters(RunViewMixin):
    @pytest.mark.parametrize("carte", [[True], [""]])
    def test_action_filters(
        self,
        rf,
        carte,
        adresses_view_class,
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

        params = {
            "action_list": [f"{action_reparer.code}|{action_preter.code}"],
            "map-latitude": [1],
            "map-longitude": [1],
            "sc_id": [sous_categorie.id],
            "carte": carte,
        }
        _, context = self._run_view(rf, adresses_view_class, params)

        assert len(context["acteurs"]) == 2

    def test_sous_categorie_filter(
        self,
        rf,
        adresses_view_class,
        sous_categorie,
        displayed_acteur_reparer,
        displayed_acteur_donner,
        displayed_acteur_preter,
    ):
        sous_categorie_id = sous_categorie.id
        params = {
            "map-latitude": [1],
            "map-longitude": [1],
            "sc_id": [str(sous_categorie_id)],
        }
        _, context = self._run_view(rf, adresses_view_class, params)

        assert DisplayedActeur.objects.count() > 1
        assert len(context["acteurs"]) == 3

    def test_sous_categorie_filter_by_action_no_match(
        self,
        rf,
        adresses_view_class,
        action_preter,
        action_reparer,
        sous_categorie,
        displayed_acteur_donner_sscat_preter_sscat2,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        sous_categorie_id = sous_categorie.id
        params = {
            "action_list": [action_preter.code],
            "map-latitude": [1],
            "map-longitude": [1],
            "sc_id": [str(sous_categorie_id)],
        }
        _, context = self._run_view(rf, adresses_view_class, params)
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert DisplayedActeur.objects.count() > 1
        assert len(context["acteurs"]) == 0

    def test_sous_categorie_filter_by_action_1_match(
        self,
        action_preter,
        action_reparer,
        sous_categorie2,
        displayed_acteur_donner_sscat_preter_sscat2,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        sous_categorie_id = sous_categorie2.id
        request.GET = query_dict_from(
            {
                "action_list": [action_preter.code],
                "map-latitude": [1],
                "map-longitude": [1],
                "sc_id": [str(sous_categorie_id)],
            }
        )
        adresses_view.setup(request)
        context = adresses_view.get_context_data()

        assert DisplayedActeur.objects.count() > 1
        assert len(context["acteurs"]) == 1


@pytest.mark.django_db
class TestBBOX:
    def test_bbox_is_returned_if_no_acteurs(self):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        map_bbox = compile_frontend_bbox([1, 1, 1, 1])
        request.GET = query_dict_from({"map-bounding_box": [map_bbox]})
        adresses_view.setup(request)
        # Initialize forms so _get_bounding_box() can access form values
        adresses_view.ui_forms = adresses_view._get_forms()

        acteurs = DisplayedActeur.objects.all()
        assert acteurs.count() == 0
        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox == map_bbox

    @override_settings(DISTANCE_MAX=100000000000)
    def test_no_bbox_and_acteurs_from_center_if_no_acteurs_found_in_bbox(
        self,
    ):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        bbox = [0, 0, 0, 0]
        map_bbox = compile_frontend_bbox(bbox)
        request.GET = query_dict_from(
            {
                "map-bounding_box": [map_bbox],
                "map-latitude": ["1"],
                "map-longitude": ["1"],
            }
        )
        adresses_view.setup(request)
        # Initialize forms so _get_bounding_box() can access form values
        adresses_view.ui_forms = adresses_view._get_forms()

        DisplayedActeurFactory.create_batch(2)
        acteurs = DisplayedActeur.objects.all()
        assert acteurs.in_bbox(bbox).count() == 0
        assert acteurs.from_center(1, 1, 100000000000).count() == 2

        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox is None
        assert acteurs.count() == 2

    def test_bbox_and_acteurs_are_returned_if_contained_in_bbox(self):
        request = HttpRequest()
        adresses_view = CarteSearchActeursView()
        bbox = [-2, -2, 4, 4]  # Acteurs in factory are created with a location of 3, 3
        map_bbox = compile_frontend_bbox(bbox)
        request.GET = query_dict_from(
            {
                "map-bounding_box": [map_bbox],
                "map-latitude": ["1"],
                "map-longitude": ["1"],
            }
        )
        adresses_view.setup(request)
        # Initialize forms so _get_bounding_box() can access form values
        adresses_view.ui_forms = adresses_view._get_forms()

        DisplayedActeurFactory.create_batch(2)
        acteurs = DisplayedActeur.objects.all()
        assert acteurs.in_bbox(bbox).count() == 2

        bbox, acteurs = adresses_view._bbox_and_acteurs_from_location_or_epci(acteurs)
        assert bbox == bbox
        assert acteurs.count() == 2


@pytest.mark.django_db
class TestLayers:
    def test_adresse_missing_layer_is_displayed(self, client, action_reparer):
        url = "/carte"
        response = client.get(url)
        assert 'data-testid="adresse-missing"' in str(response.content)

    def test_adresse_missing_layer_is_not_displayed_with_bbox(self, client):
        params = {
            "carte": 1,
            "direction": "jai",
            "bounding_box": (
                '{"southWest":{"lat":48.916,"lng":2.298202514648438},'
                '"northEast":{"lat":48.98742568330284,"lng":2.483596801757813}}'
            ),
        }
        url = f"/{urlencode(params)}"
        response = client.get(url)
        assert 'data-testid="adresse-missing"' not in str(response.content)

    def test_adresse_missing_layer_is_not_displayed_for_epcis(
        self, client, action_reparer
    ):
        params = {
            "action_list": (
                "reparer|donner|echanger|preter|emprunter|louer|"
                "mettreenlocation|acheter|revendre"
            ),
            "epci_codes": "200055887",
            "limit": "50",
        }
        url = f"/carte?{urlencode(params)}"
        response = client.get(url)

        assert 'data-testid="adresse-missing"' not in str(response.content)


@pytest.mark.django_db
class TestGetOrCreateRevisionActeur:
    def test_get_or_create_revision_acteur_only_acteur(
        self, client, acteur_type_commerce
    ):
        acteur = ActeurFactory()
        url = f"/qfdmo/getorcreate_revisionacteur/{acteur.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 302
        revision_acteur = RevisionActeur.objects.get(
            identifiant_unique=acteur.identifiant_unique
        )
        assert response.url == revision_acteur.change_url

    def test_get_or_create_revision_acteur_acteur_and_revision(self, client):
        acteur = ActeurFactory()
        revision_acteur = RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique
        )
        url = f"/qfdmo/getorcreate_revisionacteur/{acteur.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 302
        revision_acteur = RevisionActeur.objects.get(
            identifiant_unique=acteur.identifiant_unique
        )
        assert response.url == revision_acteur.change_url

    def test_get_or_create_revision_acteur_revision_parent(self, client):
        acteur = ActeurFactory()
        parent = RevisionActeur(identifiant_unique="parent12345")
        parent.save_as_parent()
        parent = RevisionActeur.objects.get(identifiant_unique="parent12345")
        print("parent", parent)
        RevisionActeurFactory(
            identifiant_unique=acteur.identifiant_unique,
            parent=parent,
        )
        url = f"/qfdmo/getorcreate_revisionacteur/{parent.identifiant_unique}"

        response = client.get(url)
        assert response.status_code == 302
        assert response.url == parent.change_url

    def test_get_or_create_revision_acteur_no_acteur(self, client):
        url = "/qfdmo/getorcreate_revisionacteur/1234567890"  # pragma: allowlist secret

        with pytest.raises((Acteur.DoesNotExist, RevisionActeur.DoesNotExist)):
            client.get(url)

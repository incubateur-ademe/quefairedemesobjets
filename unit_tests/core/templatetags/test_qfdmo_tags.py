from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point
from django.http import HttpRequest, QueryDict
from factory.django import FileField

from core.templatetags.admin_data_tags import display_diff_value
from core.templatetags.carte_tags import (
    acteur_pinpoint_tag,
    action_by_direction,
    distance_to_acteur,
)
from qfdmo.forms import ActionDirectionForm
from unit_tests.qfdmo.acteur_factory import (
    ActeurTypeFactory,
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    LabelQualiteFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory
from unit_tests.qfdmo.carte_config_factory import (
    CarteConfigFactory,
    GroupeActionConfigFactory,
)
from unit_tests.qfdmo.sscatobj_factory import SousCategorieObjetFactory


class TestActeurPinpointTag:
    @pytest.fixture
    def sous_categorie(self):
        return SousCategorieObjetFactory()

    @pytest.fixture
    def displayed_acteur(self):
        return DisplayedActeurFactory()

    @pytest.fixture
    def action_1(self):
        return ActionFactory(
            code="action1", icon="fr-icon-action-1", couleur="#c00c01", order=1
        )

    @pytest.fixture
    def action_2(self):
        return ActionFactory(
            code="action2", icon="fr-icon-action-2", couleur="#c00c02", order=2
        )

    @pytest.fixture
    def action_reparer(self):
        return ActionFactory(code="reparer")

    @pytest.fixture
    def displayed_proposition_services(
        self, sous_categorie, displayed_acteur, action_1, action_2, action_reparer
    ):
        displayed_proposition_service_1 = DisplayedPropositionServiceFactory(
            acteur=displayed_acteur,
            action=action_1,
        )
        displayed_proposition_service_1.sous_categories.add(sous_categorie)
        displayed_proposition_service_2 = DisplayedPropositionServiceFactory(
            acteur=displayed_acteur,
            action=action_2,
        )
        displayed_proposition_service_2.sous_categories.add(sous_categorie)
        displayed_proposition_service_3 = DisplayedPropositionServiceFactory(
            acteur=displayed_acteur,
            action=action_reparer,
        )
        displayed_proposition_service_3.sous_categories.add(sous_categorie)
        return [
            displayed_proposition_service_1,
            displayed_proposition_service_2,
            displayed_proposition_service_3,
        ]

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_carte_icon(
        self,
        displayed_acteur,
        action_1,
        displayed_proposition_services,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            action_1.code,
            True,
            None,
            displayed_proposition_services[0].sous_categories.first().id,
        )

        assert result_context["marker_icon"] == "fr-icon-action-1"
        assert result_context["marker_couleur"] == "#c00c01"
        assert result_context["marker_icon_file"] == ""
        assert result_context["marker_bonus"] is False
        assert result_context["marker_fill_background"] is False
        assert result_context["marker_icon_extra_classes"] == ""

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_no_action(
        self,
        displayed_acteur,
        displayed_proposition_services,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            "fake",
            True,
            None,
            displayed_proposition_services[0].sous_categories.first().id,
        )

        assert result_context["marker_icon"] == ""
        assert result_context["marker_couleur"] == ""
        assert result_context["marker_icon_file"] == ""
        assert result_context["marker_bonus"] is False
        assert result_context["marker_fill_background"] is False
        assert result_context["marker_icon_extra_classes"] == ""

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_ordered_actions(
        self,
        displayed_acteur,
        action_1,
        action_2,
        displayed_proposition_services,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-action-1"
        assert result_context["marker_couleur"] == "#c00c01"

        action_1.order = 3
        action_1.save()

        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-action-2"
        assert result_context["marker_couleur"] == "#c00c02"

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_action_principale(
        self,
        displayed_acteur,
        action_1,
        action_2,
        displayed_proposition_services,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-action-1"
        assert result_context["marker_couleur"] == "#c00c01"

        displayed_acteur.action_principale = action_2
        displayed_acteur.save()

        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-action-2"
        assert result_context["marker_couleur"] == "#c00c02"

    @pytest.fixture
    def groupe_action(self, action_1, action_2):
        groupe_action = GroupeActionFactory(
            icon="fr-icon-groupe-action", couleur="#c00c03"
        )
        groupe_action.actions.add(action_1)
        groupe_action.actions.add(action_2)
        return groupe_action

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_groupe_action(
        self,
        displayed_acteur,
        action_1,
        action_2,
        groupe_action,
        displayed_proposition_services,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-groupe-action"
        assert result_context["marker_couleur"] == "#c00c03"

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_no_carte(
        self,
        displayed_acteur,
        action_1,
        action_2,
        groupe_action,
        displayed_proposition_services,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            f"{action_1.code}|{action_2.code}",
            False,
            None,
            sous_categorie.id,
        )

        # without carte=True, groupe_action are ignored
        assert result_context["marker_icon"] == "fr-icon-action-1"
        assert result_context["marker_couleur"] == "#c00c01"

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_action_reparer(
        self,
        displayed_acteur,
        action_reparer,
        displayed_proposition_services,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            action_reparer.code,
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-tools-fill"
        assert result_context["marker_couleur"] == "#009081"
        assert result_context["marker_bonus"] is False
        assert result_context["marker_fill_background"] is True
        assert result_context["marker_icon_extra_classes"] == "qf-text-white"

        label_bonus = LabelQualiteFactory(code="label_bonus", bonus=True, afficher=True)
        # Remove cached_property to be able to test it
        del displayed_acteur.__dict__["is_bonus_reparation"]
        displayed_acteur.labels.add(label_bonus)

        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            action_reparer.code,
            True,
            None,
            sous_categorie.id,
        )

        assert result_context["marker_icon"] == "fr-icon-tools-fill"
        assert result_context["marker_couleur"] == "#009081"
        assert result_context["marker_bonus"] is True
        assert result_context["marker_fill_background"] is True
        assert result_context["marker_icon_extra_classes"] == "qf-text-white"

    @pytest.fixture
    def carte_config(self, displayed_acteur, groupe_action):
        carte_config = CarteConfigFactory()
        GroupeActionConfigFactory(
            carte_config=carte_config,
            groupe_action=groupe_action,
            acteur_type=displayed_acteur.acteur_type,
            icon=FileField(filename="top.svg"),
        )
        return carte_config

    @pytest.mark.django_db
    def test_acteur_pinpoint_tag_carte_config(
        self,
        displayed_acteur,
        displayed_proposition_services,
        action_1,
        carte_config,
        sous_categorie,
    ):
        result_context = acteur_pinpoint_tag(
            {},
            displayed_acteur,
            "",
            action_1.code,
            False,
            carte_config,
            sous_categorie.id,
        )

        assert result_context["marker_icon_file"].endswith("top.svg")
        assert result_context["marker_icon"] == ""


class TestDisplayDiffValue:
    """Tests pour la fonction display_diff_value"""

    def test_default_case_with_old_value(self, mock_diff_display):
        """Test le cas par défaut avec ancienne valeur"""
        suggestion_contexte = {"field": "old_value"}
        result = display_diff_value("field", "new_value", suggestion_contexte)

        assert result["diff_value"] == "DIFF(old_value -> new_value)"
        assert result["extra_links"] == []
        assert result["strike_value"] is None
        assert result["colored_color"] is None
        assert result["colored_value"] is None

    def test_default_case_no_old_value(self):
        """Test le cas par défaut sans ancienne valeur"""
        result = display_diff_value("field", "new_value", {})

        assert result["diff_value"] == "new_value"
        assert result["extra_links"] == []

    def test_suggestion_contexte_not_dict(self):
        """Test avec suggestion_contexte qui n'est pas un dictionnaire"""
        result = display_diff_value("field", "value", "not_a_dict")

        assert result["diff_value"] == "value"
        assert result["extra_links"] == []

    def test_non_string_http_value(self):
        """Test avec une valeur non-string qui ne commence pas par 'http'"""
        result = display_diff_value("field", 123, {})

        assert result["diff_value"] == 123
        assert result["extra_links"] == []

    @pytest.fixture
    def mock_diff_display(self):
        """Mock pour diff_display"""
        with patch("core.templatetags.admin_data_tags.diff_display") as mock:
            mock.side_effect = lambda old, new: f"DIFF({old} -> {new})"
            yield mock

    @pytest.mark.parametrize(
        "value,expected_result",
        [
            (
                None,
                {
                    "strike_value": "old_value",
                    "colored_color": "orange",
                    "colored_value": "NONE",
                    "diff_value": None,
                    "extra_links": [],
                },
            ),
            (
                "",
                {
                    "strike_value": "old_value",
                    "colored_color": "orange",
                    "colored_value": "EMPTY STRING",
                    "diff_value": None,
                    "extra_links": [],
                },
            ),
            (
                "__empty__",
                {
                    "strike_value": "old_value",
                    "colored_color": "#cb84e0",
                    "colored_value": "__empty__",
                    "diff_value": None,
                    "extra_links": [],
                },
            ),
        ],
    )
    def test_handle_empty_values(
        self,
        value,
        expected_result,  # , mock_reverse, mock_diff_display
    ):
        """Test la gestion des valeurs vides"""
        suggestion_contexte = {"key": "old_value"}
        result = display_diff_value("key", value, suggestion_contexte)
        assert result == expected_result

    def test_handle_empty_values_no_old_value(
        self,  # , mock_reverse, mock_diff_display
    ):
        """Test les valeurs vides sans ancienne valeur"""
        result = display_diff_value("key", None, {})
        expected = {
            "strike_value": None,
            "colored_color": "orange",
            "colored_value": "NONE",
            "diff_value": None,
            "extra_links": [],
        }
        assert result == expected

    @pytest.mark.parametrize(
        "key,value,expected_diff,expected_links",
        [
            (
                "source",
                "123",
                "DIFF(old_source -> 123)",
                [("/admin/qfdmo/source/123/change/", "123")],
            ),
            (
                "acteur_type",
                "456",
                "DIFF(old_acteur_type -> 456)",
                [("/admin/qfdmo/acteurtype/456/change/", "456")],
            ),
        ],
    )
    def test_handle_link_fields(
        self, key, value, expected_diff, expected_links, mock_diff_display
    ):
        """Test la gestion des champs avec liens (source, acteur_type)"""
        suggestion_contexte = {key: f"old_{key}"}
        result = display_diff_value(key, value, suggestion_contexte)

        assert result["diff_value"] == expected_diff
        assert result["extra_links"] == expected_links
        assert result["strike_value"] is None
        assert result["colored_color"] is None
        assert result["colored_value"] is None

    def test_handle_link_fields_no_old_value(self, mock_diff_display):
        """Test les champs avec liens sans ancienne valeur"""
        result = display_diff_value("source", "123", {})

        assert result["diff_value"] == "123"
        assert result["extra_links"] == [("/admin/qfdmo/source/123/change/", "123")]

    @pytest.mark.parametrize("key", ["identifiant_unique", "id"])
    def test_handle_identifiant_unique(self, key, mock_diff_display):
        """Test la gestion des champs identifiant_unique et id"""
        suggestion_contexte = {key: "old_id"}
        result = display_diff_value(key, "123", suggestion_contexte)

        expected_links = [
            ("/admin/qfdmo/acteur/123/change/", "base"),
            ("/qfdmo/getorcreate_revisionacteur/123", "revision"),
            ("/admin/qfdmo/displayedacteur/123/change/", "displayed"),
        ]

        assert result["diff_value"] == "DIFF(old_id -> 123)"
        assert result["extra_links"] == expected_links

    @pytest.mark.parametrize(
        "value,expected_color",
        [("ACTIF", "green"), ("INACTIF", "red"), ("AUTRE", "orange")],
    )
    def test_handle_statut(self, value, expected_color):
        """Test la gestion du champ statut"""
        result = display_diff_value("statut", value, {})

        assert result["colored_color"] == expected_color
        assert result["colored_value"] == value
        assert result["diff_value"] is None
        assert result["extra_links"] == []

    @pytest.mark.parametrize("value,expected_color", [(True, "red"), (False, "green")])
    def test_handle_siret_is_closed(self, value, expected_color):
        """Test la gestion du champ siret_is_closed"""
        result = display_diff_value("siret_is_closed", value, {})

        assert result["colored_color"] == expected_color
        assert result["colored_value"] == value
        assert result["diff_value"] is None
        assert result["extra_links"] == []

    def test_handle_parent(self, mock_diff_display):
        """Test la gestion du champ parent"""
        result = display_diff_value("parent", "parent_id", {})

        assert result["colored_color"] == "blue"
        assert result["colored_value"] == "parent_id (futur parent)"
        assert result["diff_value"] is None
        assert result["extra_links"] == []

    @pytest.mark.parametrize(
        "key,value,expected_url",
        [
            (
                "siren",
                "123456789",
                "https://annuaire-entreprises.data.gouv.fr/entreprise/123456789",
            ),
            (
                "siret",
                "12345678901234",
                "https://annuaire-entreprises.data.gouv.fr/etablissement/12345678901234",
            ),
        ],
    )
    def test_handle_siren_siret(self, key, value, expected_url, mock_diff_display):
        """Test la gestion des champs siren et siret"""
        suggestion_contexte = {key: f"old_{key}"}
        result = display_diff_value(key, value, suggestion_contexte)

        assert result["diff_value"] == f"DIFF(old_{key} -> {value})"
        assert result["extra_links"] == [(expected_url, value)]

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com/path",
            "http://test.fr/page?param=value",
        ],
    )
    def test_handle_http_urls(self, url, mock_diff_display):
        """Test la gestion des URLs HTTP"""
        suggestion_contexte = {"url": "old_url"}
        result = display_diff_value("url", url, suggestion_contexte)

        assert result["diff_value"] == f"DIFF(old_url -> {url})"
        assert result["extra_links"] == [(url, url)]

    def test_handle_http_urls_no_old_value(self, mock_diff_display):
        """Test les URLs HTTP sans ancienne valeur"""
        result = display_diff_value("url", "https://example.com", {})

        assert result["diff_value"] == "https://example.com"
        assert result["extra_links"] == [("https://example.com", "https://example.com")]


class TestActionByDirection:
    @pytest.mark.django_db
    def test_action_by_direction_default(self):
        request = HttpRequest()
        request.GET = QueryDict("")
        context = {
            "request": request,
            "action_direction_form": ActionDirectionForm(),
        }

        assert [
            action["libelle"] for action in action_by_direction(context, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["libelle"]
            for action in action_by_direction(context, "jai")
            if action["active"]
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]

        assert [
            action["libelle"] for action in action_by_direction(context, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["libelle"]
            for action in action_by_direction(context, "jecherche")
            if action["active"]
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]

    @pytest.mark.django_db
    def test_action_by_direction_jai(self):
        request = HttpRequest()
        request.GET = QueryDict("action_list=emprunter|louer")
        context = {
            "request": request,
            "action_direction_form": ActionDirectionForm({"direction": "jecherche"}),
        }

        assert [
            action["libelle"] for action in action_by_direction(context, "jai")
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]
        assert [
            action["libelle"]
            for action in action_by_direction(context, "jai")
            if action["active"]
        ] == [
            "prêter",
            "mettre en location",
            "réparer",
            "donner",
            "échanger",
            "vendre",
        ]

        assert [
            action["libelle"] for action in action_by_direction(context, "jecherche")
        ] == [
            "emprunter",
            "louer",
            "échanger",
            "acheter de seconde main",
        ]
        assert [
            action["libelle"]
            for action in action_by_direction(context, "jecherche")
            if action["active"]
        ] == [
            "emprunter",
            "louer",
        ]


@pytest.fixture
def adresse():
    return DisplayedActeurFactory(
        adresse="1 rue de la paix",
        location=Point(0, 0),
    )


@pytest.mark.django_db
class TestDistanceToActeur:
    @pytest.mark.parametrize(
        "request_params,expected",
        [
            (QueryDict("longitude=0&latitude=0"), "(0 m)"),
            ({"longitude": str(1051 / 111320), "latitude": "0"}, "(1,1 km)"),
            (
                {"longitude": str(1000 / 111320), "latitude": str(1000 / 111320)},
                "(1,4 km)",
            ),
            ({"longitude": str(99999 / 111320), "latitude": "0"}, "(100,0 km)"),
            (QueryDict(f"longitude={954 / 111320}&latitude=0"), "(950 m)"),
            (QueryDict(f"longitude=0&latitude=-{954 / 111320}"), "(950 m)"),
            (QueryDict(f"longitude={955 / 111320}&latitude=0"), "(960 m)"),
            (QueryDict(f"longitude={1049 / 111320}&latitude=0"), "(1,0 km)"),
            (QueryDict(f"longitude={1051 / 111320}&latitude=0"), "(1,1 km)"),
            (
                QueryDict(f"longitude={1000 / 111320}&latitude={1000 / 111320}"),
                "(1,4 km)",
            ),
            (QueryDict(f"longitude={99999 / 111320}&latitude=0"), "(100,0 km)"),
        ],
    )
    def test_distance_to_acteur_not_digital(self, adresse, request_params, expected):
        request = HttpRequest()
        request.GET = request_params
        context = {"request": request}
        assert distance_to_acteur(context, adresse) == expected

    def test_distance_to_acteur_digital(self, adresse):
        adresse.acteur_type = ActeurTypeFactory(code="acteur_digital")
        request = HttpRequest()
        request.GET = QueryDict(f"longitude={1000 / 111320}&latitude={1000 / 111320}")
        context = {"request": request}
        assert distance_to_acteur(context, adresse) == ""

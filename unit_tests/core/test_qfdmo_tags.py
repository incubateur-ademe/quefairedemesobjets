import pytest
from factory.django import FileField

from core.templatetags.qfdmo_tags import acteur_pinpoint_tag
from unit_tests.qfdmo.acteur_factory import (
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

        assert result_context["marker_icon_file"] == (
            "/media/config/groupeaction/icones/top.svg"
        )
        assert result_context["marker_icon"] == ""

from typing import List, cast

from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.forms import model_to_dict

from qfdmo.models.utils import CodeAsNaturalKeyModel


class ActionDirection(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Direction de l'action"
        verbose_name_plural = "Directions de l'action"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    order = models.IntegerField(blank=False, null=False, default=0)
    libelle = models.CharField(max_length=255, unique=True, blank=False, null=False)

    def __str__(self):
        return self.libelle


class GroupeAction(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Groupe d'actions"
        verbose_name_plural = "Groupes d'actions"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    afficher = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(blank=False, null=False, default=0)
    couleur = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="yellow-tournesol",
        help_text="""Couleur du badge à choisir dans le DSFR
Couleurs disponibles : blue-france, green-tilleul-verveine, green-bourgeon,
green-emeraude, green-menthe, green-archipel, blue-ecume, blue-cumulus, purple-glycine,
pink-macaron, pink-tuile, yellow-tournesol, yellow-moutarde, orange-terre-battue,
brown-cafe-creme,brown-caramel, brown-opera, beige-gris-galet, pink-tuile-850,
green-menthe-850,green-bourgeon-850, yellow-moutarde-850, blue-ecume-850,
green-menthe-sun-373,blue-cumulus-sun-368, orange-terre-battue-main-645,
brown-cafe-creme-main-782, purple-glycine-main-494, green-menthe-main-548
""",
    )
    icon = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Icône du badge à choisir dans le <a href='https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/icones' rel='noopener' target='_blank'>DSFR</a>",  # noqa E501
    )

    @property
    def libelle(self):
        return ", ".join({a.libelle_groupe for a in self.actions.all()}).capitalize()


class Action(CodeAsNaturalKeyModel):
    class Meta:
        ordering = ["order"]

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    libelle = models.CharField(max_length=255, null=False, default="")
    libelle_groupe = models.CharField(
        max_length=255,
        null=False,
        default="",
        blank=True,
        help_text="Libellé de l'action dans le groupe",
    )
    afficher = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(blank=False, null=False, default=0)
    directions = models.ManyToManyField(ActionDirection, related_name="actions")
    couleur = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="yellow-tournesol",
        help_text="""Couleur du badge à choisir dans le DSFR
Couleurs disponibles : blue-france, green-tilleul-verveine, green-bourgeon,
green-emeraude, green-menthe, green-archipel, blue-ecume, blue-cumulus, purple-glycine,
pink-macaron, pink-tuile, yellow-tournesol, yellow-moutarde, orange-terre-battue,
brown-cafe-creme,brown-caramel, brown-opera, beige-gris-galet, pink-tuile-850,
green-menthe-850,green-bourgeon-850, yellow-moutarde-850, blue-ecume-850,
green-menthe-sun-373,blue-cumulus-sun-368, orange-terre-battue-main-645,
brown-cafe-creme-main-782, purple-glycine-main-494, green-menthe-main-548
""",
    )
    icon = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Icône du badge à choisir dans le <a href='https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/icones' rel='noopener' target='_blank'>DSFR</a>",  # noqa E501
    )
    groupe_action = models.ForeignKey(
        GroupeAction,
        on_delete=models.CASCADE,
        related_name="actions",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.libelle


def get_action_instances() -> List[Action]:
    return list(Action.objects.prefetch_related("directions", "groupe_action"))


def get_reparer_action_id() -> int:
    try:
        return [
            action for action in get_action_instances() if action.code == "reparer"
        ][0].id
    except IndexError:
        raise Exception("Action 'Réparer' not found")


def get_groupe_action_instances() -> QuerySet[GroupeAction]:
    return GroupeAction.objects.prefetch_related("actions").order_by("order")


def get_actions_by_direction() -> dict:
    return {
        d.code: sorted(
            [
                model_to_dict(a, exclude=["directions"])
                for a in d.actions.filter(afficher=True)
            ],
            key=lambda x: x["order"],
        )
        for d in ActionDirection.objects.all()
    }


def get_directions() -> List[dict]:
    direction_instances = ActionDirection.objects.all()
    directions_list = [model_to_dict(d) for d in direction_instances]
    return sorted(directions_list, key=lambda x: x["order"])


def get_ordered_directions(first_direction=None) -> List[dict]:
    ordered_directions = cast(
        List[dict], cache.get_or_set("directions", get_directions)
    )
    if first_direction is not None and first_direction in [
        d["code"] for d in ordered_directions
    ]:
        return sorted(
            ordered_directions,
            key=lambda x: (x["code"] != first_direction, x["code"]),
        )
    return ordered_directions

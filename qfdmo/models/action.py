from typing import List, cast

from colorfield.fields import ColorField
from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.forms import model_to_dict
from django.utils.functional import cached_property

from dsfr_hacks.colors import DSFRColors
from qfdmo.models.utils import CodeAsNaturalKeyManager, CodeAsNaturalKeyModel


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


class GroupeActionQueryset(models.QuerySet):
    def as_codes(self, concat=True):
        actions = []

        for groupe in self:
            actions = [*actions, *groupe.actions.all().values_list("code", flat=True)]

        if concat:
            return "|".join(actions)

        return actions


class GroupeActionManager(CodeAsNaturalKeyManager):
    def get_queryset(self):
        return GroupeActionQueryset(self.model, using=self._db)


COLOR_PALETTE = list(DSFRColors.items())


class GroupeAction(CodeAsNaturalKeyModel):
    objects = GroupeActionManager()

    class Meta:
        verbose_name = "Groupe d'actions"
        verbose_name_plural = "Groupes d'actions"

    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    afficher = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(blank=False, null=False, default=0)
    couleur = ColorField(
        null=True, blank=True, default="#C3992A", max_length=255, choices=COLOR_PALETTE
    )

    couleur_claire = ColorField(
        null=True, blank=True, default="#C3992A", max_length=255, choices=COLOR_PALETTE
    )

    @cached_property
    def primary(self):
        return next(
            (
                key
                for key, value in DSFRColors.items()
                if value.lower() == self.couleur.lower()
            ),
            "",
        )

    @cached_property
    def secondary(self):
        return next(
            (
                key
                for key, value in DSFRColors.items()
                if value.lower() == self.couleur_claire.lower()
            ),
            None,
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
    couleur = ColorField(
        null=True,
        blank=True,
        default="#C3992A",
        max_length=255,
        choices=COLOR_PALETTE,
        help_text="Cette couleur est utilisée uniquement pour"
        " la version formulaire (épargnons).",
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

    @cached_property
    def primary(self):
        return next(
            (
                key
                for key, value in DSFRColors.items()
                if value.lower() == self.couleur.lower()
            ),
            "",
        )

    @cached_property
    def secondary(self):
        return self.primary

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
    # TODO: refactor to not use a dict anymore
    return {
        d.code: sorted(
            [
                {**model_to_dict(a, exclude=["directions"]), "primary": a.primary}
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

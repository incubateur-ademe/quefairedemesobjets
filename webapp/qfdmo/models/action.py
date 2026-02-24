from typing import List, cast

from colorfield.fields import ColorField
from django.contrib.gis.db import models
from django.core.cache import cache
from django.db.models import CheckConstraint, Q
from django.forms import model_to_dict
from django.utils.functional import cached_property

from dsfr_hacks.colors import DSFRColors
from qfdmo.models.utils import CodeAsNaturalKeyManager, CodeAsNaturalKeyModel
from qfdmo.validators import CodeValidator


# TODO: the direction form used in Formulaire now uses an enum
# This model could be migrated to an enum at some point.
class ActionDirection(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "Action - Direction"
        constraints = [
            CheckConstraint(
                condition=Q(code__regex=CodeValidator.regex),
                name="action_direction_code_format",
            ),
        ]

    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
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


COLOR_PALETTE = [(hexa.upper(), color) for color, hexa in DSFRColors.items()]


class GroupeAction(CodeAsNaturalKeyModel):
    objects = GroupeActionManager()

    class Meta:
        # Prefix to group action objects in the admin side panel
        verbose_name = "Action - Groupe d'action"
        verbose_name_plural = "Action - Groupes d'action"
        constraints = [
            CheckConstraint(
                condition=Q(code__regex=CodeValidator.regex),
                name="groupe_action_code_format",
            ),
        ]

    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
    afficher = models.BooleanField(default=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(blank=False, null=False, default=0)
    couleur = ColorField(
        null=True, blank=True, default="#C3992A", max_length=255, choices=COLOR_PALETTE
    )

    couleur_claire = ColorField(
        null=True, blank=True, default="#C3992A", max_length=255, choices=COLOR_PALETTE
    )
    fill = models.BooleanField(
        default=False,
        verbose_name="Remplissage du fond",
        help_text="Ce champ permet de configurer un groupe d'action"
        " pour que son icône dispose d'un fond plein plutôt qu'un fond ajouré.\n"
        "C'est ce qui est utilisé par exemple sur l'action réparer",
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

    def get_libelle_from(self, actions):
        return ", ".join({a.libelle_groupe for a in actions}).capitalize()

    def get_libelle_from_config(self, carte_config):
        actions = self.actions.all()

        if not carte_config:
            return self.get_libelle_from(actions)

        if config_actions := carte_config.action.all():
            actions = actions.filter(id__in=config_actions)

        if config_directions := carte_config.direction.all():
            actions = actions.filter(directions__in=config_directions)

        if config_groupes := carte_config.groupe_action.all():
            actions = actions.filter(groupe_action__in=config_groupes)

        return self.get_libelle_from(actions)

    @property
    def libelle(self):
        return self.get_libelle_from(self.actions.all())


class Action(CodeAsNaturalKeyModel):
    class Meta:
        # Prefix to group action objects in the admin side panel
        verbose_name = "Action - Action"
        ordering = ["order"]
        constraints = [
            CheckConstraint(
                condition=Q(code__regex=CodeValidator.regex),
                name="action_code_format",
            ),
        ]

    id = models.AutoField(primary_key=True)
    code = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        null=False,
        help_text=(
            "Ce champ est utilisé lors de l'import de données, il ne doit pas être"
            " mis à jour sous peine de casser l'import de données"
        ),
        validators=[CodeValidator()],
    )
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
    return Action.objects.prefetch_related("directions", "groupe_action")


def get_reparer_action_id() -> int:
    try:
        return [
            action for action in get_action_instances() if action.code == "reparer"
        ][0].id
    except IndexError:
        raise Exception("Action 'Réparer' not found")


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


def get_ordered_directions() -> List[dict]:
    return cast(List[dict], cache.get_or_set("directions", get_directions))

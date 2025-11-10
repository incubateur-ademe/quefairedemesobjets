from typing import List, cast

from colorfield.fields import ColorField
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db.models import CheckConstraint, Q, TextChoices
from django.forms import model_to_dict
from django.utils.functional import cached_property

from dsfr_hacks.colors import DSFRColors
from qfdmo.models.utils import CodeAsNaturalKeyManager, CodeAsNaturalKeyModel
from qfdmo.validators import CodeValidator


class Direction(TextChoices):
    J_AI = ("jai", "J'ai un objet")
    JE_CHERCHE = ("jecherche", "Je recherche un objet")


class ActionDirection(CodeAsNaturalKeyModel):
    class Meta:
        verbose_name = "[DEPRECIE] Action - Direction"
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
    direction_codes = ArrayField(
        models.CharField(
            max_length=32,
            choices=Direction.choices,
        ),
        default=list,
        blank=True,
        null=False,
    )
    directions = models.ManyToManyField(
        ActionDirection,
        related_name="actions",
        blank=True,
        help_text="[DEPRECIE] Relation historique entre `Action` et `ActionDirection`. "
        "Merci d'utiliser l'énumération `Direction` et le champ `direction_codes`.",
    )
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

    def has_direction(self, code: str) -> bool:
        return code in self.direction_codes


def get_action_instances() -> List[Action]:
    return list(Action.objects.prefetch_related("groupe_action").all())


def get_reparer_action_id() -> int:
    try:
        return [
            action for action in get_action_instances() if action.code == "reparer"
        ][0].id
    except IndexError:
        raise Exception("Action 'Réparer' not found")


def get_actions_by_direction() -> dict[str, list[dict]]:
    cached_actions = [action for action in get_action_instances() if action.afficher]
    actions_by_direction: dict[str, list[dict]] = {}

    for direction in Direction:
        actions = [
            {**model_to_dict(a, exclude=["direction_codes"]), "primary": a.primary}
            for a in cached_actions
            if direction.value in a.direction_codes
        ]
        actions_by_direction[direction.value] = sorted(
            actions, key=lambda x: x["order"]
        )

    return actions_by_direction


# TODO: check if it is useful & if we can remove the order notions
def get_directions() -> List[dict]:
    """
    Retourne la liste des directions connues avec priorité à l'enum `Direction`.
    Les enregistrements supplémentaires dans la table historique sont conservés.
    """

    ordered: list[dict] = []
    for index, direction in enumerate(Direction, start=1):
        ordered.append(
            {
                "code": direction.value,
                "libelle": direction.label,
                "order": index,
            }
        )

    return sorted(ordered, key=lambda x: x["order"])


def get_ordered_directions() -> List[dict]:
    return cast(List[dict], cache.get_or_set("directions", get_directions))

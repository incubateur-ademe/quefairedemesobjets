import time
from typing import List

from django.contrib.gis.db import models
from django.forms import model_to_dict

from qfdmo.models.utils import CodeAsNaturalKeyModel


class CachedDirectionAction:
    _cached_actions_by_direction = None
    _cached_actions = None
    _cached_direction = None
    _reparer_action_id = None
    _last_cache_update = None

    @classmethod
    def get_actions(cls) -> dict:
        cls._manage_cache_expiration()
        if cls._cached_actions is None:
            cls._cached_actions = {
                a.code: {
                    **model_to_dict(a, exclude=["directions"]),
                    "directions": [d.code for d in a.directions.all()],
                }
                for a in Action.objects.all()
            }

        return cls._cached_actions

    @classmethod
    def get_actions_by_direction(cls) -> dict:
        cls._manage_cache_expiration()
        if cls._cached_actions_by_direction is None:
            cls._cached_actions_by_direction = {
                d.code: sorted(
                    [
                        model_to_dict(a, exclude=["directions"])
                        for a in d.actions.filter(afficher=True)
                    ],
                    key=lambda x: x["order"],
                )
                for d in ActionDirection.objects.all()
            }

        return cls._cached_actions_by_direction

    @classmethod
    def get_directions(cls, first_direction=None) -> List[dict]:
        cls._manage_cache_expiration()
        if cls._cached_direction is None:
            directions = ActionDirection.objects.all()
            directions_list = [model_to_dict(d) for d in directions]
            sorted_directions = sorted(directions_list, key=lambda x: x["order"])
            cls._cached_direction = sorted_directions
        if first_direction is not None and first_direction in [
            d["code"] for d in cls._cached_direction
        ]:
            return sorted(
                cls._cached_direction,
                key=lambda x: (x["code"] != first_direction, x["code"]),
            )
        return cls._cached_direction

    @classmethod
    def get_reparer_action_id(cls):
        cls._manage_cache_expiration()
        if cls._reparer_action_id is None:
            cls._reparer_action_id = Action.objects.get(code="reparer").id
        return cls._reparer_action_id

    @classmethod
    def reload_cache(cls):
        cls._cached_actions_by_direction = None
        cls._cached_actions = None
        cls._cached_direction = None
        cls._reparer_action_id = None

    @classmethod
    def _manage_cache_expiration(cls):
        if cls._last_cache_update is None:
            cls._last_cache_update = time.time()
            return

        current_time = time.time()
        if current_time - cls._last_cache_update > 300:
            cls.reload_cache()
            cls._last_cache_update = current_time


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


class Action(CodeAsNaturalKeyModel):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255, unique=True, blank=False, null=False)
    libelle = models.CharField(max_length=255, null=False, default="")
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
Couleur dispoible : blue-france, green-tilleul-verveine, green-bourgeon, green-emeraude,
green-menthe, green-archipel, blue-ecume, blue-cumulus, purple-glycine, pink-macaron,
pink-tuile, yellow-tournesol, yellow-moutarde, orange-terre-battue, brown-cafe-creme,
brown-caramel, brown-opera, beige-gris-galet""",
    )
    icon = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Icône du badge à choisir dans le <a href='https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/icones' rel='noopener' target='_blank'>DSFR</a>",  # noqa E501
    )

    def __str__(self):
        return self.libelle

    def serialize(self):
        return model_to_dict(self, exclude=["directions"])

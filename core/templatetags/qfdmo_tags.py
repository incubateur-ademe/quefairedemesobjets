import logging
from math import sqrt

from diff_match_patch import diff_match_patch
from django.contrib.admin.utils import quote
from django.db.models import Q
from django.template.defaulttags import register
from django.urls.base import reverse
from django.utils.safestring import mark_safe

from core.utils import get_direction
from qfdmo.models import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction
from qfdmo.models.config import GroupeActionConfig

logger = logging.getLogger(__name__)


@register.simple_tag
def actions_for(dispayed_acteur: DisplayedActeur, direction):
    return dispayed_acteur.acteur_actions(direction=direction)


@register.simple_tag(takes_context=True)
def action_by_direction(context, direction):
    """Get action for the given direction following context"""
    request = context["request"]
    requested_direction = get_direction(request)
    action_displayed = request.GET.get("action_displayed", "")
    actions_to_display = get_actions_by_direction()[direction]

    if action_displayed:
        actions_to_display = [
            a for a in actions_to_display if a["code"] in action_displayed.split("|")
        ]

    if action_list := (
        None if requested_direction != direction else request.GET.get("action_list")
    ):
        return [
            {
                **a,
                "active": bool(a["code"] in action_list),
            }
            for a in actions_to_display
        ]
    return [{**a, "active": True} for a in actions_to_display]


@register.simple_tag(takes_context=True)
def hide_object_filter(context):
    """should hide the object filter?"""
    request = context["request"]
    return (
        bool(request.GET.get("sc_id"))
        and request.GET.get("map_container_id") != "carte"
    )


@register.simple_tag(takes_context=True)
def distance_to_acteur(context, acteur):
    """distance from user location to displayed acteur"""
    request = context["request"]
    longitude = request.GET.get("longitude")
    latitude = request.GET.get("latitude")
    location = acteur.location

    if not (longitude and latitude and location and not acteur.is_digital):
        return ""

    distance_meters = (
        sqrt((location.y - float(latitude)) ** 2 + (location.x - float(longitude)) ** 2)
        * 111320
    )
    if distance_meters >= 1000:
        return f"({round(distance_meters / 1000, 1)} km)".replace(".", ",")
    else:
        return f"({round(distance_meters / 10) * 10} m)"


@register.filter
def diff_display(old_value, new_value):
    """
    Template filter pour afficher les différences entre deux valeurs en utilisant
    diff-match-patch.
    """
    if old_value == new_value:
        return str(new_value)

    dmp = diff_match_patch()
    diffs = dmp.diff_main(str(old_value), str(new_value))
    dmp.diff_cleanupSemantic(diffs)

    result = []
    for op, text in diffs:
        if op == 0:  # égal
            result.append(text)
        elif op == -1:  # supprimé
            result.append(
                f'<span style="color: red; text-decoration: line-through;">{text}'
                "</span>"
            )
        elif op == 1:  # ajouté
            result.append(f'<span style="color: green;">{text}</span>')

    return mark_safe("".join(result))


@register.inclusion_tag("data/_partials/display_diff_value.html")
def display_diff_value(key, value, suggestion_contexte):
    """Display diff value with context links"""

    def _get_diff_value(old_value_exists, old_value, value):
        """Compute the diff value to display"""
        if old_value_exists:
            return diff_display(old_value, value)
        else:
            return value

    def _handle_empty_values(value, old_value):
        """Handle empty or None values"""
        if value is None:
            return {
                "strike_value": old_value,
                "colored_color": "orange",
                "colored_value": "NONE",
            }
        elif value == "":
            return {
                "strike_value": old_value,
                "colored_color": "orange",
                "colored_value": "EMPTY STRING",
            }
        elif value == "__empty__":
            return {
                "strike_value": old_value,
                "colored_color": "#cb84e0",
                "colored_value": "__empty__",
            }
        return None

    def _handle_link_fields(key, value, old_value_exists, old_value):
        """Handle fields that generate links (source, acteur_type)"""
        url_map = {
            "source": reverse("admin:qfdmo_source_change", args=[value]),
            "acteur_type": reverse("admin:qfdmo_acteurtype_change", args=[value]),
        }
        if key in ["source", "acteur_type"]:
            return {
                "diff_value": _get_diff_value(old_value_exists, old_value, value),
                "extra_links": [(url_map[key], value)],
            }
        return {}

    def _handle_identifiant_unique(value, old_value_exists, old_value):
        """Handle identifiant_unique and id fields"""
        extra_links = [
            (reverse("admin:qfdmo_acteur_change", args=[value]), "base"),
            (reverse("qfdmo:getorcreate_revisionacteur", args=[value]), "revision"),
            (reverse("admin:qfdmo_displayedacteur_change", args=[value]), "displayed"),
        ]
        return {
            "diff_value": _get_diff_value(old_value_exists, old_value, value),
            "extra_links": extra_links,
        }

    def _handle_statut(value):
        """Handle statut field with colors"""
        color_map = {"ACTIF": "green", "INACTIF": "red"}
        return {"colored_color": color_map.get(value, "orange"), "colored_value": value}

    def _handle_siret_is_closed(value):
        """Handle siret_is_closed field"""
        return {
            "colored_color": "green" if not value else "red",
            "colored_value": value,
        }

    def _handle_parent(value):
        """Handle parent field"""
        return {"colored_color": "blue", "colored_value": f"{value} (futur parent)"}

    def _handle_siren_siret(key, value, old_value_exists, old_value):
        """Handle siren and siret fields with links to annuaire-entreprises"""
        url_map = {
            "siren": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{value}",
            "siret": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{value}",
        }
        return {
            "diff_value": _get_diff_value(old_value_exists, old_value, value),
            "extra_links": [(url_map[key], value)],
        }

    def _handle_http_urls(value, old_value_exists, old_value):
        """Handle HTTP URLs"""
        return {
            "diff_value": _get_diff_value(old_value_exists, old_value, value),
            "extra_links": [(value, value)],
        }

    old_value_exists = (
        isinstance(suggestion_contexte, dict) and key in suggestion_contexte
    )
    old_value = suggestion_contexte.get(key, None) if old_value_exists else None

    # Initialize default values
    result = {
        "strike_value": None,
        "colored_color": None,
        "colored_value": None,
        "diff_value": None,
        "extra_links": [],
    }

    # Gestion des valeurs vides
    empty_result = _handle_empty_values(value, old_value)
    if empty_result:
        result.update(empty_result)
        return result

    # Gestion par type de champ
    if key in ["source", "acteur_type"]:
        result.update(_handle_link_fields(key, value, old_value_exists, old_value))
    elif key in ["identifiant_unique", "id"]:
        result.update(_handle_identifiant_unique(value, old_value_exists, old_value))
    elif key == "statut":
        result.update(_handle_statut(value))
    elif key == "siret_is_closed":
        result.update(_handle_siret_is_closed(value))
    elif key == "parent":
        result.update(_handle_parent(value))
    elif key in ["siren", "siret"]:
        result.update(_handle_siren_siret(key, value, old_value_exists, old_value))
    elif isinstance(value, str) and value.startswith("http"):
        result.update(_handle_http_urls(value, old_value_exists, old_value))
    else:
        # Cas par défaut
        result["diff_value"] = _get_diff_value(old_value_exists, old_value, value)

    return result


@register.filter
def valuetype(value):
    return type(value).__name__


@register.filter
def tojson(value):
    """Django filter to replace Jinja2's |tojson filter"""
    import json

    return json.dumps(value)


@register.filter
def title_case(value):
    """Django filter to properly handle title case like Jinja2"""
    if value:
        return value.title()
    return value


@register.simple_tag
def random_range(max_value):
    """Generate a random number for cache busting"""
    import random

    return random.randint(0, max_value - 1)


@register.inclusion_tag("qfdmo/carte/pinpoints/acteur.html", takes_context=True)
def acteur_pinpoint_tag(
    context, acteur, direction, action_list, carte, carte_config, sous_categorie_id
):
    """
    Template tags to display the acteur's pinpoint after increasing context with
      - marker_icon
      - marker_couleur
      - marker_icon_file
      - marker_bonus
      - marker_fill_background
      - marker_icon_extra_classes
    """
    context.update(
        {
            "marker_icon": "",
            "marker_couleur": "",
            "marker_icon_file": "",
            "marker_bonus": False,
            "marker_fill_background": False,
            "marker_icon_extra_classes": "",
        }
    )

    action_to_display = acteur.action_to_display(
        direction=direction,
        action_list=action_list,
        sous_categorie_id=sous_categorie_id,
    )
    if action_to_display is None:
        logger.warning("No actions found for acteur %s", acteur)
        return context

    if carte_config:
        queryset = Q()
        if action_to_display:
            queryset &= Q(
                groupe_action__actions__code__in=[action_to_display.code]
            ) | Q(groupe_action__actions__code=None)

        if acteur.acteur_type:
            queryset &= Q(acteur_type=acteur.acteur_type) | Q(acteur_type=None)

        try:
            groupe_action_config = carte_config.groupe_action_configs.get(queryset)
            if groupe_action_config.icon:
                # Property is camelcased as it is used in javascript
                context.update(
                    {
                        "marker_icon_file": groupe_action_config.icon.url,
                        "marker_icon": "",
                    }
                )
                return context

        except GroupeActionConfig.DoesNotExist:
            pass

    if carte:
        if action_to_display.groupe_action:
            action_to_display = action_to_display.groupe_action
        if action_to_display.code == "reparer":
            context.update(
                {
                    "marker_bonus": getattr(acteur, "is_bonus_reparation", False),
                    "marker_fill_background": True,
                    "marker_icon_extra_classes": "qf-text-white",
                }
            )

    context.update(
        {
            "marker_icon": action_to_display.icon,
            "marker_couleur": action_to_display.couleur,
        }
    )

    return context


@register.simple_tag
def get_non_enseigne_labels_count(acteur):
    """Template tag to get count of labels with type_enseigne=False"""
    return acteur.labels_display.filter(type_enseigne=False).count()


@register.filter(name="quote")
def quote_filter(value):
    return quote(value)

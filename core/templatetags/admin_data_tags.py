import logging

from diff_match_patch import diff_match_patch
from django.contrib.admin.utils import quote
from django.template.defaulttags import register
from django.urls.base import reverse
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


@register.filter
def diff_display(old_value, new_value):
    """
    Template filter pour afficher les différences entre deux valeurs en utilisant
    diff-match-patch.
    """
    if old_value == new_value:
        if new_value == "":
            return "-"
        return str(new_value)

    dmp = diff_match_patch()
    diffs = dmp.diff_main(str(old_value), str(new_value))
    dmp.diff_cleanupSemantic(diffs)

    result = []
    for op, text in diffs:
        if op == 0:  # égal
            result.append(text)
        elif op == -1:  # supprimé
            result.append(f'<span class="suggestion-text-removed">{text}</span>')
        elif op == 1:  # ajouté
            result.append(f'<span class="suggestion-text-added">{text}</span>')
    result = "".join(result)
    if result == "":
        result = "-"
    return mark_safe(result)


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


@register.filter(name="quote")
def quote_filter(value):
    return quote(value)


@register.filter
def display_diff_values(old_value: str | None, new_value: str):
    if not old_value:
        return diff_display("", new_value)
    return diff_display(old_value, new_value)


@register.inclusion_tag("data/_partials/extra_links.html")
def extra_links(field, value, default_value):
    if value is None:
        value = default_value
    if field in ["siren", "siret"]:
        url_map = {
            "siren": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{value}",
            "siret": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{value}",
        }
        return {
            "extra_links": [(url_map[field], value)],
        }
    elif isinstance(value, str) and value.startswith("http"):
        return {"extra_links": [(value, value)]}
    return {}

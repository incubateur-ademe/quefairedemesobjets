from django import template

from core.constants import MAP_CONTAINER_ID

register = template.Library()


@register.inclusion_tag("ui/components/modals/_modal_button.html", takes_context=True)
def modal_button(context, modal_id, button_text="", button_extra_classes=""):
    """
    Renders a button that opens a DSFR modal.

    Args:
        modal_id: The unique ID of the modal to open (will be automatically namespaced)
        button_text: The text to display on the button
        button_extra_classes: Additional CSS classes for the button

    Usage:
        {% load modal_tags %}
        {% modal_button modal_id="infos" button_text="Infos" %}
    """
    # Apply namespacing to the modal_id if a namespace exists in context
    if MAP_CONTAINER_ID in context:
        namespaced_modal_id = f"{context.get(MAP_CONTAINER_ID)}:{modal_id}"
    else:
        namespaced_modal_id = modal_id

    return {
        "modal_id": namespaced_modal_id,
        "button_text": button_text,
        "button_extra_classes": button_extra_classes,
    }

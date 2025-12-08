from django.template.defaulttags import register

from core.constants import DEFAULT_MAP_CONTAINER_ID, MAP_CONTAINER_ID


@register.simple_tag(takes_context=True)
def main_frame_id(context: dict) -> str:
    """
    Get the main Turbo Frame ID for the current carte instance.
    Used to identify the primary turbo-frame container, enabling multiple independent
    carte instances on the same page (e.g., embedded iframes). Defaults to "carte".
    """
    return context.get(MAP_CONTAINER_ID, DEFAULT_MAP_CONTAINER_ID)


@register.simple_tag(takes_context=True)
def namespaced(context: dict, id: str) -> str:
    """
    Create a namespaced ID scoped to the current carte instance.
    Used to generate unique element IDs (forms, modals, etc.) when multiple carte
    instances exist on the same page, preventing ID collisions.
    """
    if MAP_CONTAINER_ID not in context:
        return id
    return f"{context.get(MAP_CONTAINER_ID)}:{id}"

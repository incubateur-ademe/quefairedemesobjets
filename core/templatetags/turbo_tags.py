from django.template.defaulttags import register

from core.constants import MAP_CONTAINER_ID


@register.simple_tag(takes_context=True)
def acteur_frame_id(context):
    return f"{context.get(MAP_CONTAINER_ID)}:acteur-detail"


@register.simple_tag(takes_context=True)
def main_frame_id(context):
    return context.get(MAP_CONTAINER_ID, "carte")

from django.template.defaulttags import register

from core.constants import MAP_CONTAINER_ID


@register.simple_tag(takes_context=True)
def main_frame_id(context):
    return context.get(MAP_CONTAINER_ID, "carte")


@register.simple_tag(takes_context=True)
def namespaced(context, id):
    return f"{context.get(MAP_CONTAINER_ID)}:{id}"


@register.simple_tag(takes_context=True)
def acteur_frame_id(context):
    return namespaced(context, "acteur-detail")

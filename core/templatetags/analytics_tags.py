from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("ui/analytics/matomo.html")
def matomo(id):
    return {"matomo_url": "stats.beta.gouv.fr", "matomo_id": id}


@register.inclusion_tag("ui/analytics/posthog_data_attributes.html")
def posthog_data_attributes(key):
    debug = settings.POSTHOG_DEBUG
    return {"key": key, "debug": debug}

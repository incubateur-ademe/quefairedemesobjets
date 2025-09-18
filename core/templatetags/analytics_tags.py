from django import template

register = template.Library()


@register.inclusion_tag("analytics/matomo.html")
def matomo(id):
    return {"matomo_url": "stats.beta.gouv.fr", "matomo_id": id}


@register.inclusion_tag("analytics/posthog_data_attributes.html")
def posthog_data_attributes(key):
    return {"key": key}

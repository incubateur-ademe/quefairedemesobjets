from django.conf import settings
from django.utils.encoding import force_str
from django.utils.functional import Promise
from wagtail.fields import DjangoJSONEncoder

from qfdmo.models.action import get_directions


def get_direction(request, is_carte=False):
    default_direction = None if is_carte else settings.DEFAULT_ACTION_DIRECTION
    direction = request.GET.get("direction", default_direction)
    if direction not in [d["code"] for d in get_directions()]:
        direction = default_direction
    return direction


class LazyEncoder(DjangoJSONEncoder):
    """
    Force lazy strings to text

    Inspired by https://github.com/hiimdoublej/django-json-ld/blob/master/django_json_ld/util.py
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_str(obj)
        return super(LazyEncoder, self).default(obj)

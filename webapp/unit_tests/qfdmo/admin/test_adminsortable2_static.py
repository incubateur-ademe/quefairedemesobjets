from django import VERSION
from django.contrib.staticfiles import finders


def test_adminsortable2_has_actions_js_for_this_django():
    """adminsortable2 swaps admin/js/actions.js for a copy named after the Django
    version: without it, the LabelQualite list crashes in production."""
    assert finders.find("adminsortable2/js/actions-{}.{}.js".format(*VERSION))

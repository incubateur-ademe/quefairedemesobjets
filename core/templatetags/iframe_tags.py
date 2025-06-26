from django import template
from django.http.request import QueryDict

register = template.Library()


@register.filter
def iframe(querydict: QueryDict, template_path: str):
    """
    Conditionally returns an iframe-specific template path based on query parameters.

    This Django template filter checks whether the `"iframe"` parameter is present
    in the provided query dictionary (typically `request.GET`). If it is, the function
    returns a modified version of the `template_path` by replacing `.html` with
    `.iframe.html`. Otherwise, it returns the original path.

    :param querydict: The GET parameters from the request (e.g., ``request.GET``).
    :type querydict: django.http.QueryDict
    :param template_path: The path to the default
    template (e.g., ``"components/header/base.html"``).
    :type template_path: str
    :return: The modified or original template path depending on the
    presence of ``"iframe"`` in the query.
    :rtype: str

    **Example usage in a Django template**::

        {% extends request.GET|iframe:"components/header/base.html" %}

    This would extend either ``base.html`` or ``base.iframe.html`` depending on whether
    ``?iframe`` is in the URL query string.
    """
    alternative_path = template_path.replace("html", "iframe.html")

    if "iframe" in querydict:
        return alternative_path

    return template_path

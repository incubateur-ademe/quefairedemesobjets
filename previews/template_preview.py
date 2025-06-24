# Ignore line length recommandations from flake8
# flake8: noqa: E501
from django.template.loader import render_to_string
from django_lookbook.preview import LookbookPreview


class AssistantPreview(LookbookPreview):
    def header(self, **kwargs):
        """
        `includes/header.html` is a partial template, we can write preview for it in this way.

        **Markdown syntax is supported in docstring**
        """
        return render_to_string("components/header/header.html")

    def footer(self, **kwargs):
        """
        We can write template code directly
        """
        return render_to_string("components/footer/footer.html")

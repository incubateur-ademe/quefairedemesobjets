import logging

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class GroupeActionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(
            render_to_string(
                "forms/widgets/groupe_action_label.html",
                {"groupe_action": obj},
            )
        )


class EPCIField(forms.MultipleChoiceField):
    def to_python(self, value):
        # TODO : once multiple EPCI codes will be managed, this method will be useless
        # and the frontend will be rewritten to support a more complex state with all
        # values matching their labels.
        python_value = super().to_python(value)
        return [value.split(" - ")[1] for value in python_value]

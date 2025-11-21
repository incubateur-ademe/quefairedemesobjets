import logging

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class GroupeActionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        try:
            libelle = obj.get_libelle_from_config(self.widget.carte_config)
        except AttributeError:
            libelle = obj.libelle
        return mark_safe(
            render_to_string(
                "ui/forms/widgets/groupe_action_label.html",
                {"groupe_action": obj, "libelle": libelle},
            )
        )


class LabelQualiteChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(
            render_to_string(
                "ui/forms/widgets/label_qualite_label.html",
                {"label_qualite": obj},
            )
        )

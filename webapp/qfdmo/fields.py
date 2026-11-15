import logging

from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from core.templatetags.external_link_tags import announce_new_window_links

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
                {
                    "label_qualite": obj,
                    "texte_d_aide": mark_safe(
                        announce_new_window_links(obj.filtre_texte_d_aide)
                    ),
                },
            )
        )

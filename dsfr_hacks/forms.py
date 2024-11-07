from django import forms
from pydantic import ValidationError

from dsfr_hacks.colors import DSFRColors


class DSFRColorField(forms.CharField):
    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super().validate(value)
        try:
            DSFRColors[value]
        except KeyError:
            raise ValidationError("La couleur n'existe pas dans les couleurs du DSFR")


class ColorForm(forms.Form):
    hexa_color = forms.CharField()
    dsfr_color = forms.CharField()

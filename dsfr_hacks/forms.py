from django import forms
from dsfr.forms import DsfrBaseForm


class ColorForm(DsfrBaseForm):
    hexa_color = forms.CharField(label="Couleur hexadécimale")

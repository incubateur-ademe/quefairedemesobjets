from django import forms
from dsfr.forms import DsfrBaseForm

from .constants import CATEGORIE_CHOICES, CONSIGNE_CHOICES


class InfotriForm(DsfrBaseForm):
    """Form for Info-tri generator configuration."""

    categorie = forms.ChoiceField(
        choices=CATEGORIE_CHOICES,
        label="",
        required=False,
        widget=forms.RadioSelect(),
    )

    consigne = forms.ChoiceField(
        choices=CONSIGNE_CHOICES,
        label="",
        required=False,
        widget=forms.RadioSelect(),
    )

    avec_phrase = forms.BooleanField(
        label="Afficher la phrase",
        required=False,
        widget=forms.CheckboxInput(),
    )

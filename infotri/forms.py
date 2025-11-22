from django import forms
from dsfr.forms import DsfrBaseForm

from .constants import CATEGORIE_CHOICES, CONSIGNE_CHOICES


class InfotriForm(DsfrBaseForm):
    """Form for Info-tri generator configuration."""

    categorie = forms.ChoiceField(
        choices=CATEGORIE_CHOICES,
        label="Choisissez une catégorie de produit",
        required=False,
        widget=forms.RadioSelect(
            attrs={
                "class": "fr-radio-group",
                "data-infotri-target": "categorieInput",
                "data-action": "change->infotri#updateCategorie",
            }
        ),
    )

    consigne = forms.ChoiceField(
        choices=CONSIGNE_CHOICES,
        label="Choisissez la consigne",
        required=False,
        widget=forms.RadioSelect(
            attrs={
                "class": "fr-radio-group",
                "data-infotri-target": "consigneInput",
                "data-action": "change->infotri#updateConsigne",
            }
        ),
    )

    avec_phrase = forms.BooleanField(
        label="Afficher la phrase",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "fr-toggle__input",
                "data-infotri-target": "avecPhraseInput",
                "data-action": "change->infotri#updateAvecPhrase",
            }
        ),
    )

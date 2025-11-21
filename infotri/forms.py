from django import forms
from dsfr.forms import DsfrBaseForm


class InfotriForm(DsfrBaseForm):
    """Form for Info-tri generator configuration."""

    CATEGORIE_CHOICES = [
        ("", "Sélectionnez une catégorie"),
        ("tous", "Tous"),
        ("chaussures", "Chaussures"),
        ("vetement", "Vêtement"),
        ("tissu", "Tissu"),
    ]

    CONSIGNE_CHOICES = [
        ("", "Sélectionnez une consigne"),
        ("1", "À déposer dans un conteneur"),
        ("2", "À déposer dans un conteneur ou dans une association"),
        (
            "3",
            "À déposer dans un conteneur, dans une association ou dans"
            " un magasin volontaire",
        ),
    ]

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

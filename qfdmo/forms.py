from django import forms

from qfdmo.models import SousCategorieObjet


class AutoCompleteInput(forms.Select):
    template_name = "autocomplete.html"


class GetReemploiSolutionForm(forms.Form):
    sous_categorie_objet = forms.ModelChoiceField(
        queryset=SousCategorieObjet.objects.all(),
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Vêtement, Meuble, Smartphone, etc.",
                # FIXME : id can be removed ?
                "id": "myInput",
            }
        ),
        label="",
        empty_label="",
    )
    adresse = forms.CharField(
        label="Adresse",
        widget=forms.TextInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Entrez ici votre adresse",
                "css_class": "fr-col-12",
            },
        ),
    )

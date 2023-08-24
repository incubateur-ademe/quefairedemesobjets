from django import forms

from qfdmo.models import SousCategorieObjet


class AutoCompleteInput(forms.Select):
    template_name = "autocomplete.html"

    def __init__(self, attrs=None, max_options_displayed=10, **kwargs):
        self.max_options_displayed = max_options_displayed
        super().__init__(attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["max_options_displayed"] = self.max_options_displayed
        return context


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
        required=False,
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

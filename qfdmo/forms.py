from django import forms

from qfdmo.models import SousCategorieObjet


class AutoCompleteInput(forms.Select):
    template_name = "autocomplete.html"

    def __init__(
        self, attrs=None, max_options_displayed=10, search_callback=False, **kwargs
    ):
        self.max_options_displayed = max_options_displayed
        self.search_callback = search_callback
        super().__init__(attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["max_options_displayed"] = self.max_options_displayed
        if self.search_callback:
            context["widget"]["search_callback"] = "true"
        return context


class GetReemploiSolutionForm(forms.Form):
    sous_categorie_objet = forms.ModelChoiceField(
        queryset=SousCategorieObjet.objects.all(),
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Vêtement, Meuble, Smartphone, etc.",
            }
        ),
        label="",
        empty_label="",
        required=False,
    )
    adresse = forms.CharField(
        widget=AutoCompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "Quelle est votre adresse ?",
            },
            search_callback=True,
            max_options_displayed=5,
        ),
        label="",
        required=False,
    )

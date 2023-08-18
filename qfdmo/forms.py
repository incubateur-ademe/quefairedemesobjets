from django import forms

# from qfdmo.models import SousCategorieObjet


class FooForm(forms.Form):
    # sous_categorie_objet = forms.ModelChoiceField(
    #     queryset=SousCategorieObjet.objects.all(),
    #     widget=forms.Select(attrs={"class": "fr-select"}),
    #     label="Sélectionnez…",
    # )
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

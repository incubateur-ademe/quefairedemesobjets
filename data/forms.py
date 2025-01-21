from django import forms

from data.models import SuggestionCohorte, SuggestionStatut


class SuggestionCohorteForm(forms.Form):
    suggestion_cohorte = forms.ModelChoiceField(
        label="Séléctionner l'execution d'un DAG",
        widget=forms.Select(
            attrs={
                "class": "fr-select",
            }
        ),
        queryset=SuggestionCohorte.objects.filter(
            statut=SuggestionStatut.AVALIDER.value
        ),
        required=True,
    )

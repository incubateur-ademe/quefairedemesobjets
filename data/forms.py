from django import forms


class SuggestionGroupeForm(forms.Form):
    suggestion_modele = forms.CharField(widget=forms.HiddenInput())
    champs = forms.CharField(widget=forms.HiddenInput())
    valeurs = forms.CharField(widget=forms.HiddenInput(), required=False)


class SuggestionGroupeStatusForm(forms.Form):
    action = forms.ChoiceField(
        choices=[("validate", "À Traiter"), ("reject", "Rejeter")]
    )

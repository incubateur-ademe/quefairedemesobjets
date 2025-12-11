from django import forms


class SuggestionGroupeStatusForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("validate", "À Traiter"),
            ("reject", "Rejeter"),
            ("to_process", "Renvoyer à traiter"),
        ]
    )

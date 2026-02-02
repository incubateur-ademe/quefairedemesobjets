import logging
from typing import Any

from django import forms
from dsfr.forms import DsfrBaseForm

from core.widgets import HeaderSearchAutocompleteInput

from .mixins import HomeSearchMixin

logger = logging.getLogger(__name__)


class SearchInput(forms.TextInput):
    template_name = "ui/components/search/widget.html"


class HomeSearchForm(HomeSearchMixin, DsfrBaseForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput())
    input = forms.CharField(
        help_text="Entrez un objet ou un déchet",
        required=False,
        widget=SearchInput,
    )

    def search(self, beta: bool) -> list[dict[str, Any]]:
        """Main search method that orchestrates the search process."""
        search_query = self.cleaned_data.get("input")
        if not search_query:
            return []

        if beta:
            self.results = self.search_home(search_query)
        else:
            self.results = self._search_synonymes(search_query)
        return self.results


class HeaderSearchForm(DsfrBaseForm):
    search = forms.CharField(
        required=False,
        widget=HeaderSearchAutocompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "pantalon, perceuse, canapé...",
                "autocomplete": "off",
            },
        ),
    )


class ContactForm(DsfrBaseForm):
    name = forms.CharField(label="Votre nom")
    name.widget.attrs["autocomplete"] = "name"
    email = forms.EmailField(label="Votre email")
    email.widget.attrs["autocomplete"] = "email"
    subject = forms.ChoiceField(
        label="Votre sujet",
        choices=[
            ("", "Sélectionner une option"),
            (
                "integration",
                "Je souhaite obtenir de l'aide pour intégrer cet outil",
            ),
            (
                "erreur",
                "Je souhaite signaler une erreur pour un déchet",
            ),
            (
                "manquant",
                "Je souhaite signaler un déchet manquant",
            ),
            (
                "bug",
                "J'ai trouvé un bug",
            ),
            (
                "amelioration",
                "Je souhaite proposer une amélioration",
            ),
            (
                "autre",
                "Autre",
            ),
        ],
    )
    message = forms.CharField(
        label="Votre message", widget=forms.Textarea(attrs={"rows": 4})
    )

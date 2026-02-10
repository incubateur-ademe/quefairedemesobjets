import logging

from django import forms
from dsfr.forms import DsfrBaseForm
from modelsearch.query import Fuzzy

from search.models import SearchTerm

logger = logging.getLogger(__name__)


class SearchInput(forms.TextInput):
    template_name = "ui/components/search/widget.html"


class SearchForm(DsfrBaseForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput())
    input = forms.CharField(
        help_text="Entrez un objet ou un déchet",
        required=False,
        widget=SearchInput,
    )

    def search(self) -> list:
        self.results = []
        search_query = self.cleaned_data.get("input")
        if not search_query:
            self.results = []
            return self.results

        self.results = SearchTerm.objects.search(Fuzzy(search_query))[:10]
        return self.results


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

import logging

from django import forms
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import (
    TrigramSimilarity,
    TrigramStrictWordSimilarity,
)
from django.db.models import Case, F, Value, When
from dsfr.forms import DsfrBaseForm

from .models import Synonyme

logger = logging.getLogger(__name__)


class SearchInput(forms.TextInput):
    template_name = "components/search/widget.html"


class SearchForm(DsfrBaseForm):
    input = forms.CharField(
        help_text="Entrez un objet ou un déchet", required=False, widget=SearchInput
    )
    iframe = forms.BooleanField(
        required=False,
        help_text="Ce champ sert uniquement à faire persister le mode iframe d'une page"
        "à une recherche",
        widget=forms.HiddenInput,
    )

    def search(self) -> dict[str, str]:
        search_query: str = self.cleaned_data.get("input")
        self.results = (
            Synonyme.objects.annotate(
                word_similarity=TrigramStrictWordSimilarity(search_query, "nom"),
                similarity=TrigramSimilarity("nom", search_query),
                unaccented_nom=Unaccent("nom"),
                boosted_score=Case(
                    When(
                        unaccented_nom__istartswith=search_query,
                        then=F("similarity") + Value(0.1),
                    ),
                    When(
                        unaccented_nom__iendswith=search_query,
                        then=F("similarity") + Value(0.05),
                    ),
                    default=F("similarity"),
                ),
            )
            .filter(word_similarity__gte=0.1)
            .order_by("-boosted_score", "-word_similarity", "-similarity")
            .values("slug", "nom")[:10]
        )
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

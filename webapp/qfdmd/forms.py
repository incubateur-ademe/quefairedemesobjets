import logging
import uuid

from django import forms
from dsfr.forms import DsfrBaseForm

from core.widgets import QfSearchAutocompleteInput, SearchAutocompleteInput

logger = logging.getLogger(__name__)


class HeaderSearchForm(DsfrBaseForm):
    """DSFR-styled search form used in the site header."""

    search = forms.CharField(
        required=False,
        widget=SearchAutocompleteInput(
            attrs={
                "class": "fr-input",
                "placeholder": "pantalon, perceuse, canapé...",
                "autocomplete": "off",
            },
        ),
    )


class QfSearchForm(forms.Form):
    """Quefaire-styled search form used on the homepage.

    Intentionally does NOT inherit DsfrBaseForm to avoid DSFR injecting
    fr-input class and its label/wrapper markup.
    """

    search = forms.CharField(
        required=False,
        label="",
        widget=QfSearchAutocompleteInput(
            attrs={
                "placeholder": "exemple : canapé, téléphone, CD-ROM...",
                "autocomplete": "off",
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate a fresh turbo_frame_id per instance so that multiple forms
        # on the same page don't share the same turbo-frame element ID.
        self.fields["search"].widget.turbo_frame_id = str(uuid.uuid4())


# TODO: backward compatibility only
class HomeSearchForm(HeaderSearchForm):
    pass


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

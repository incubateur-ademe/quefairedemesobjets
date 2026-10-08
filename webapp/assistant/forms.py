"""Forms of the assistant.

The objet + address pair is typed through autocomplete: the visible field
carries a label, the hidden fields carry what the server actually uses, the
targeted fiche and the coordinates. Validating both together is a form's job,
not a chain of `if` in the view.

The parameters of the places endpoint are validated by `api.LieuxQuery`.
"""

from django import forms

from assistant.objets import fiche_for_label
from qfdmd.models import ProduitPage

UNKNOWN_OBJET_MESSAGE = (
    "Nous ne connaissons pas cet objet. Choisissez une suggestion dans la liste."
)
MISSING_ADRESSE_MESSAGE = "Indiquez une adresse ou une commune."


class SearchForm(forms.Form):
    """What the home page sends to open a fiche.

    `fiche` is a `ModelChoiceField`: the form therefore yields a `ProduitPage`,
    not a string every caller would have to resolve again, and the field itself
    checks that the fiche exists.

    It is declared optional in Django's sense but required in the business
    sense: it can be inferred from the label when the user arrives through a
    shared URL without going through the autocomplete. `clean()` decides.
    """

    objet = forms.CharField(required=False, max_length=200)
    fiche = forms.ModelChoiceField(
        # `to_field_name` makes the form carry the slug rather than the primary
        # key: the URL stays readable and shareable.
        queryset=ProduitPage.objects.live(),
        to_field_name="slug",
        required=False,
        error_messages={"invalid_choice": UNKNOWN_OBJET_MESSAGE},
    )
    adresse = forms.CharField(required=False, max_length=200)
    longitude = forms.FloatField(required=False)
    latitude = forms.FloatField(required=False)
    precise = forms.BooleanField(required=False)

    def clean_adresse(self) -> str:
        adresse = (self.cleaned_data.get("adresse") or "").strip()
        if not adresse:
            raise forms.ValidationError(MISSING_ADRESSE_MESSAGE)
        return adresse

    def clean(self):
        data = super().clean()
        if data.get("fiche") is None:
            data["fiche"] = self._fiche_from_label(data)
        return data

    def _fiche_from_label(self, data: dict) -> ProduitPage:
        """The fiche the label designates, when the autocomplete set none.

        A shared URL only carries the label: "?objet=Téléphone mobile" must
        open the fiche, not send the user back to a form that looks filled but
        refuses to move on.

        The label is not a fiche title but a search term ("Téléphone mobile"
        leads to "Téléphones, tablettes ou consoles"): it is resolved through
        the same path as the autocomplete, otherwise the two would diverge.
        """
        label = (data.get("objet") or "").strip()
        fiche = fiche_for_label(label) if label else None
        if fiche is None:
            raise forms.ValidationError({"objet": UNKNOWN_OBJET_MESSAGE})
        return fiche

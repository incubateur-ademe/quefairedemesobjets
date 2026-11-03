"""The home search: an objet (a label, and the fiche when a suggestion was
chosen) and an optional address, which must come from a suggestion."""

from django import forms

from assistant.objets import fiche_for_label
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage

UNKNOWN_OBJET_MESSAGE = (
    "Nous ne connaissons pas cet objet. Choisissez une suggestion dans la liste."
)
MISSING_OBJET_MESSAGE = "Veuillez d'abord saisir un objet ou un déchet"
UNKNOWN_ADRESSE_MESSAGE = (
    "Nous ne connaissons pas cette adresse. Choisissez une suggestion dans la liste."
)
MISSING_ADRESSE_MESSAGE = (
    "Saisissez une adresse pour voir les solutions près de chez vous."
)


class SearchForm(forms.Form):
    """Yields the `ProduitPage` to open. `fiche` is optional for Django: a
    shared URL may carry only the label, from which `clean()` infers it."""

    objet = forms.CharField(required=False, max_length=200)
    fiche = forms.ModelChoiceField(
        queryset=ProduitPage.objects.live(),
        to_field_name="slug",
        required=False,
        error_messages={"invalid_choice": UNKNOWN_OBJET_MESSAGE},
    )
    adresse = forms.CharField(required=False, max_length=200)

    def clean(self):
        data = super().clean()
        # Typed text without coordinates: no suggestion was chosen.
        parcours = Parcours.from_query(self.data)
        if parcours.adresse and not parcours.is_located:
            self.add_error("adresse", UNKNOWN_ADRESSE_MESSAGE)
        if data.get("fiche") is None:
            data["fiche"] = self._fiche_from_label(data)
        return data

    def _fiche_from_label(self, data: dict) -> ProduitPage:
        """The fiche a label designates (a search term, not a fiche title),
        when no suggestion set it."""
        label = (data.get("objet") or "").strip()
        if not label:
            raise forms.ValidationError({"objet": MISSING_OBJET_MESSAGE})
        fiche = fiche_for_label(label)
        if fiche is None:
            raise forms.ValidationError({"objet": UNKNOWN_OBJET_MESSAGE})
        return fiche

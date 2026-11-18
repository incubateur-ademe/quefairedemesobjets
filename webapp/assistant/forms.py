"""The home search: an objet (a label, and the fiche when a suggestion was
chosen) and an optional address, which must come from a suggestion."""

from django import forms

from assistant.objets import fiche_for_label
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage

MISSING_OBJET_MESSAGE = "Veuillez d'abord saisir un objet ou un déchet"
MISSING_ADRESSE_MESSAGE = (
    "Saisissez une adresse pour voir les solutions près de chez vous."
)


def no_result_message(text: str) -> str:
    return f"Aucun résultat pour «\u00a0{text}\u00a0»"


class SearchForm(forms.Form):
    """Yields the `ProduitPage` to open. `fiche` is optional for Django: a
    shared URL may carry only the label, from which `clean()` infers it."""

    objet = forms.CharField(required=False, max_length=200)
    fiche = forms.ModelChoiceField(
        queryset=ProduitPage.objects.live(),
        to_field_name="slug",
        required=False,
    )
    adresse = forms.CharField(required=False, max_length=200)

    def clean(self):
        data = super().clean()
        # Typed text without coordinates: no suggestion was chosen.
        parcours = Parcours.from_query(self.data)
        if parcours.adresse and not parcours.is_located:
            self.add_error("adresse", no_result_message(parcours.adresse))
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
            raise forms.ValidationError({"objet": no_result_message(label)})
        return fiche

"""Forms of the assistant.

The objet is typed through autocomplete: the visible field carries a label,
the hidden field the targeted fiche. The address is optional and travels in
the URL; once typed, it must come from a suggestion, which carries its
coordinates.

The parameters of the places endpoint are validated by `api.LieuxQuery`.
"""

from django import forms

from assistant.objets import fiche_for_label
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage

UNKNOWN_OBJET_MESSAGE = (
    "Nous ne connaissons pas cet objet. Choisissez une suggestion dans la liste."
)
# Nothing typed is not an unknown objet: the mockup has its own wording (30144:16015).
MISSING_OBJET_MESSAGE = "Veuillez d'abord saisir un objet ou un déchet"
UNKNOWN_ADRESSE_MESSAGE = (
    "Nous ne connaissons pas cette adresse. Choisissez une suggestion dans la liste."
)


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
    # Optional: declared so that `clean()` can attach its error to the field.
    adresse = forms.CharField(required=False, max_length=200)

    def clean(self):
        data = super().clean()
        # The address is optional, but typed text without coordinates means no
        # suggestion was chosen: searching would silently ignore it.
        parcours = Parcours.from_query(self.data)
        if parcours.adresse and not parcours.is_located:
            self.add_error("adresse", UNKNOWN_ADRESSE_MESSAGE)
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
        if not label:
            raise forms.ValidationError({"objet": MISSING_OBJET_MESSAGE})
        fiche = fiche_for_label(label)
        if fiche is None:
            raise forms.ValidationError({"objet": UNKNOWN_OBJET_MESSAGE})
        return fiche

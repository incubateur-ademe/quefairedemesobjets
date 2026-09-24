"""Forms of the assistant.

The objet + address pair is typed through autocomplete: the visible field
carries a label, the hidden fields carry what the server actually uses, the
targeted fiche and the coordinates. Validating both together is a form's job,
not a chain of `if` in the view.
"""

import math

from django import forms
from django.core.exceptions import ValidationError

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


BBOX_CORNERS = (
    ("southWest", "lng", 180),
    ("southWest", "lat", 90),
    ("northEast", "lng", 180),
    ("northEast", "lat", 90),
)


class LieuxForm(forms.Form):
    """Query parameters of the places endpoint.

    The position is either the visible area (`bbox`, as sent by the map) or a
    point (`lon`, `lat`). An unreadable bbox is refused rather than falling
    back on the point: the fallback would hide a client bug and show an area
    the user is not looking at.
    """

    # ponytail: not validated against GroupeAction, that would cost the
    # endpoint its single query. Add a ChoiceField when the geste page lands.
    geste = forms.CharField()
    objet = forms.SlugField(required=False)
    bbox = forms.JSONField(required=False)
    lon = forms.FloatField(required=False, min_value=-180, max_value=180)
    lat = forms.FloatField(required=False, min_value=-90, max_value=90)

    def clean_bbox(self) -> list[float] | None:
        raw = self.cleaned_data["bbox"]
        if raw is None:
            return None
        try:
            bbox = [float(raw[corner][axis]) for corner, axis, _ in BBOX_CORNERS]
        except (KeyError, TypeError, ValueError):
            raise ValidationError("unreadable bbox")
        for value, (_, _, bound) in zip(bbox, BBOX_CORNERS):
            if not math.isfinite(value) or abs(value) > bound:
                raise ValidationError("bbox out of range")
        return bbox

    def clean(self):
        data = super().clean()
        if data.get("bbox") is None and None in (data.get("lon"), data.get("lat")):
            raise ValidationError("bbox or lon/lat required")
        return data

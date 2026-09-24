import math

from django import forms
from django.core.exceptions import ValidationError

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

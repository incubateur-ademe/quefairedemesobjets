from django import forms

SUGGESTED_CITIES = (
    "Paris",
    "Lyon",
    "Marseille",
    "Bordeaux",
    "Lille",
    "Strasbourg",
    "Nantes",
    "Rennes",
    "Brest",
    "Ajaccio",
    "Chambéry",
)


class AdresseDatalistInput(forms.TextInput):
    """Address field with native suggestions, for the lookbook forms.

    The lookbook parameter panel lives outside the preview iframe and only
    loads the lookbook's JavaScript: the project's Stimulus autocomplete
    (`CarteAddressAutocompleteInput`) would not work there. A native
    `<datalist>` offers the same convenience without a Stimulus application.

    The suggestions are a fixed list of common cities; any other text is
    geocoded as is by the preview.
    """

    template_name = "previews/widgets/adresse_datalist.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_id"] = f"{attrs.get('id', name)}-suggestions"
        context["widget"]["suggestions"] = SUGGESTED_CITIES
        return context

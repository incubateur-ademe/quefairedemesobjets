from django import forms

from qfdmo.views.autocomplete import BAN_API_URL, BAN_TIMEOUT_SECONDS

VILLES_SUGGEREES = (
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
    """Champ adresse avec suggestions natives, pour les formulaires du lookbook.

    Le panneau de paramètres du lookbook vit hors de l'iframe de preview et ne
    charge que le JavaScript du lookbook : l'autocomplete Stimulus du projet
    (`CarteAddressAutocompleteInput`) n'y fonctionnerait pas. Un `<datalist>`
    natif offre la même commodité sans dépendre d'une application Stimulus.

    La liste combine des villes courantes et, si l'usager a déjà saisi quelque
    chose, les propositions de la BAN pour cette saisie.
    """

    template_name = "previews/widgets/adresse_datalist.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["datalist_id"] = f"{attrs.get('id', name)}-suggestions"
        context["widget"]["suggestions"] = self._suggestions(value)
        return context

    def _suggestions(self, saisie) -> list[str]:
        propositions = list(VILLES_SUGGEREES)
        for adresse in self._adresses_ban(saisie):
            if adresse not in propositions:
                propositions.append(adresse)
        return propositions

    def _adresses_ban(self, saisie) -> list[str]:
        """Libellés proposés par la BAN, ou rien si elle est indisponible.

        L'échec est silencieux : ces suggestions sont un confort de saisie dans
        un outil de développement, leur absence ne doit pas casser la preview.
        """
        if not saisie or len(str(saisie)) < 3:
            return []

        import requests

        try:
            reponse = requests.get(
                BAN_API_URL,
                params={"q": str(saisie), "limit": 5},
                timeout=BAN_TIMEOUT_SECONDS,
            )
            reponse.raise_for_status()
            features = reponse.json().get("features", [])
        except (requests.RequestException, ValueError):
            return []

        return [
            feature["properties"]["label"]
            for feature in features
            if "label" in feature.get("properties", {})
        ]

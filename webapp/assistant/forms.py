"""Formulaire de recherche de l'assistant.

Le couple objet + adresse est saisi en autocomplétion : le champ visible porte
un libellé, les champs cachés portent ce que le serveur exploite réellement —
le slug de la fiche, les coordonnées. Valider les deux ensemble est le travail
d'un formulaire, pas d'une suite de `if` dans la vue.
"""

from django import forms

from assistant.views.recherche import slug_du_libelle

MESSAGE_OBJET_INCONNU = (
    "Nous ne connaissons pas cet objet. Choisissez une suggestion dans la liste."
)
MESSAGE_ADRESSE_MANQUANTE = "Indiquez une adresse ou une commune."


class RechercheForm(forms.Form):
    """Ce que l'accueil envoie pour ouvrir une fiche.

    `slug` est facultatif au sens du formulaire mais requis au sens métier : il
    peut être déduit du libellé quand l'usager arrive par une URL partagée,
    sans être passé par l'autocomplétion. C'est `clean()` qui tranche.
    """

    objet = forms.CharField(required=False, max_length=200)
    slug = forms.CharField(required=False, max_length=200)
    adresse = forms.CharField(required=False, max_length=200)
    longitude = forms.FloatField(required=False)
    latitude = forms.FloatField(required=False)
    precise = forms.BooleanField(required=False)

    def clean_adresse(self) -> str:
        adresse = (self.cleaned_data.get("adresse") or "").strip()
        if not adresse:
            raise forms.ValidationError(MESSAGE_ADRESSE_MANQUANTE)
        return adresse

    def clean(self):
        donnees = super().clean()
        donnees["slug"] = self._slug_de(donnees)
        return donnees

    def _slug_de(self, donnees: dict) -> str:
        """Le slug choisi, ou celui que le libellé permet de retrouver.

        Une URL partagée ne porte que le libellé : « ?objet=Téléphone mobile »
        doit ouvrir la fiche, pas renvoyer l'usager vers un formulaire qui
        semble rempli mais refuse d'avancer.

        Le libellé n'est pas un titre de fiche mais un terme de recherche
        (« Téléphone mobile » mène à « Téléphones, tablettes ou consoles ») :
        on le résout par le même chemin que l'autocomplétion, sinon les deux
        divergeraient.
        """
        if slug := (donnees.get("slug") or "").strip():
            return slug

        libelle = (donnees.get("objet") or "").strip()
        if not libelle:
            raise forms.ValidationError({"objet": MESSAGE_OBJET_INCONNU})

        slug = slug_du_libelle(libelle)
        if not slug:
            raise forms.ValidationError({"objet": MESSAGE_OBJET_INCONNU})
        return slug

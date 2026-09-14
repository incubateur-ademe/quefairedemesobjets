"""Formulaire de recherche de l'assistant.

Le couple objet + adresse est saisi en autocomplétion : le champ visible porte
un libellé, les champs cachés portent ce que le serveur exploite réellement —
la fiche visée, les coordonnées. Valider les deux ensemble est le travail d'un
formulaire, pas d'une suite de `if` dans la vue.
"""

from django import forms

from assistant.objets import fiche_du_libelle
from qfdmd.models import ProduitPage

MESSAGE_OBJET_INCONNU = (
    "Nous ne connaissons pas cet objet. Choisissez une suggestion dans la liste."
)
MESSAGE_ADRESSE_MANQUANTE = "Indiquez une adresse ou une commune."


class RechercheForm(forms.Form):
    """Ce que l'accueil envoie pour ouvrir une fiche.

    `fiche` est un `ModelChoiceField` : le formulaire rend donc une
    `ProduitPage`, pas une chaîne que chaque appelant devrait re-résoudre, et
    l'existence de la fiche est vérifiée par le champ lui-même.

    Il est déclaré non requis au sens de Django mais l'est au sens métier : il
    peut être déduit du libellé quand l'usager arrive par une URL partagée,
    sans être passé par l'autocomplétion. C'est `clean()` qui tranche.
    """

    objet = forms.CharField(required=False, max_length=200)
    fiche = forms.ModelChoiceField(
        # `to_field_name` fait porter au formulaire le slug plutôt que la clé
        # primaire : l'URL reste lisible et partageable.
        queryset=ProduitPage.objects.live(),
        to_field_name="slug",
        required=False,
        error_messages={"invalid_choice": MESSAGE_OBJET_INCONNU},
    )
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
        if donnees.get("fiche") is None:
            donnees["fiche"] = self._fiche_depuis_le_libelle(donnees)
        return donnees

    def _fiche_depuis_le_libelle(self, donnees: dict) -> ProduitPage:
        """La fiche que le libellé désigne, quand l'autocomplétion n'a rien posé.

        Une URL partagée ne porte que le libellé : « ?objet=Téléphone mobile »
        doit ouvrir la fiche, pas renvoyer l'usager vers un formulaire qui
        semble rempli mais refuse d'avancer.

        Le libellé n'est pas un titre de fiche mais un terme de recherche
        (« Téléphone mobile » mène à « Téléphones, tablettes ou consoles ») :
        on le résout par le même chemin que l'autocomplétion, sinon les deux
        divergeraient.
        """
        libelle = (donnees.get("objet") or "").strip()
        fiche = fiche_du_libelle(libelle) if libelle else None
        if fiche is None:
            raise forms.ValidationError({"objet": MESSAGE_OBJET_INCONNU})
        return fiche

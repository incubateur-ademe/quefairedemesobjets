from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from assistant.consignes import consignes_pour
from assistant.forms import RechercheForm
from assistant.lieu import gestes_de, infos_pratiques_de, propose_le_bonus
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction

from .mixins import TurboFrameMixin


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"

    def get(self, request, *args, formulaire=None, **kwargs):
        """`formulaire` est passé par `RechercheView` quand la saisie est
        refusée : l'accueil se réaffiche alors avec ses messages."""
        self.formulaire = formulaire
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            parcours=Parcours.depuis(self.request.GET),
            erreurs=getattr(self, "formulaire", None) and self.formulaire.errors,
            **kwargs,
        )


class RechercheView(View):
    """Reçoit le formulaire d'accueil et oriente vers la fiche de l'objet.

    Une redirection plutôt qu'un rendu : l'URL finale est celle de la fiche,
    donc partageable, rechargeable et correcte dans l'historique.

    Une saisie incomplète revient à l'accueil avec ce qui a déjà été tapé,
    plutôt que d'afficher une erreur sur un formulaire vidé.
    """

    def get(self, request, *args, **kwargs):
        formulaire = RechercheForm(request.GET)
        if not formulaire.is_valid():
            # Réafficher l'accueil avec ses erreurs, plutôt qu'y rediriger : une
            # redirection perdrait les messages et l'usager verrait un
            # formulaire rempli qui refuse d'avancer, sans savoir pourquoi.
            return HomeView.as_view()(request, formulaire=formulaire)

        parcours = Parcours.depuis(request.GET)
        destination = reverse(
            "assistant:produit", kwargs={"slug": formulaire.cleaned_data["slug"]}
        )
        return redirect(f"{destination}?{urlencode(parcours.en_parametres())}")


class ProduitView(TurboFrameMixin, DetailView):
    model = ProduitPage
    template_name = "ui/pages/assistant/produit.html"
    context_object_name = "produit"

    def get_queryset(self):
        return ProduitPage.objects.live()

    def get_context_data(self, **kwargs):
        parcours = Parcours.depuis(self.request.GET)
        return super().get_context_data(
            parcours=parcours,
            parametres=urlencode(parcours.en_parametres()),
            consignes=consignes_pour(self.object, parcours),
            **kwargs,
        )


class SolutionsView(TurboFrameMixin, TemplateView):
    """Écran carte : les lieux proposant le geste choisi, autour de l'adresse.

    La carte ne reçoit pas de lieux au rendu : elle les demande elle-même en
    GeoJSON une fois la toile prête, et les redemande à chaque déplacement
    (#3356). Les servir ici les figerait au premier affichage.
    """

    template_name = "ui/pages/assistant/solutions.html"

    def get_context_data(self, **kwargs):
        parcours = Parcours.depuis(self.request.GET)
        geste = (self.request.GET.get("geste") or "").strip()
        slug = (self.request.GET.get("slug") or "").strip()
        groupe = GroupeAction.objects.filter(code=geste).first()

        longitude, latitude = _position_de(parcours)
        return super().get_context_data(
            parcours=parcours,
            geste=geste,
            # L'endpoint GeoJSON attend le slug de la fiche, pas le libellé
            # saisi : c'est lui qui porte les sous-catégories.
            slug=slug,
            libelle_geste=(groupe.libelle_court or groupe.libelle) if groupe else "",
            couleur_geste=groupe.couleur if groupe else "",
            url_fiche=self._url_fiche(parcours),
            # Le lien d'une punaise emporte le parcours : sans lui, « Revenir
            # aux solutions » perdrait le geste et l'adresse.
            parametres_lieu=urlencode(
                {**parcours.en_parametres(), "geste": geste, "slug": slug}
            ),
            longitude=longitude,
            latitude=latitude,
            # La punaise rouge n'apparaît que pour une adresse précise (#3356).
            adresse_precise=parcours.precise and parcours.localise,
            **kwargs,
        )

    def _url_fiche(self, parcours: Parcours) -> str:
        """Retour vers la fiche de l'objet, ou l'accueil si on ne sait plus lequel."""
        slug = (self.request.GET.get("slug") or "").strip()
        parametres = urlencode(parcours.en_parametres())
        if not slug:
            return f"{reverse('assistant:home')}?{parametres}"
        destination = reverse("assistant:produit", kwargs={"slug": slug})
        return f"{destination}?{parametres}"


# Centre par défaut : la France entière, quand l'adresse n'a pas été géocodée.
CENTRE_PAR_DEFAUT = (2.3488, 48.8534)


def _position_de(parcours: Parcours) -> tuple[float, float]:
    if parcours.localise:
        return parcours.longitude, parcours.latitude
    return CENTRE_PAR_DEFAUT


class LieuView(TurboFrameMixin, DetailView):
    model = DisplayedActeur
    template_name = "ui/pages/assistant/lieu.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "lieu"

    def get_queryset(self):
        return DisplayedActeur.objects.all().pour_le_detail()

    def get_context_data(self, **kwargs):
        parcours = Parcours.depuis(self.request.GET)
        # Le retour vers les solutions doit retrouver le geste et l'objet, que
        # le parcours seul ne porte pas.
        retour = {
            **parcours.en_parametres(),
            **{
                cle: valeur
                for cle in ("geste", "slug")
                if (valeur := (self.request.GET.get(cle) or "").strip())
            },
        }
        return super().get_context_data(
            parcours=parcours,
            parametres=urlencode(retour),
            infos_pratiques=infos_pratiques_de(self.object),
            bonus_reparation=propose_le_bonus(self.object),
            gestes=gestes_de(self.object),
            **kwargs,
        )

from urllib.parse import urlencode

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from assistant.parcours import Parcours
from qfdmd.models import ProduitPage
from qfdmo.models.acteur import DisplayedActeur

from .mixins import TurboFrameMixin


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            parcours=Parcours.depuis(self.request.GET), **kwargs
        )


class RechercheView(View):
    """Reçoit le formulaire d'accueil et oriente vers la fiche de l'objet.

    Une redirection plutôt qu'un rendu : l'URL finale est celle de la fiche,
    donc partageable, rechargeable et correcte dans l'historique.

    Une saisie incomplète revient à l'accueil avec ce qui a déjà été tapé,
    plutôt que d'afficher une erreur sur un formulaire vidé.
    """

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        parcours = Parcours.depuis(request.GET)
        slug = (request.GET.get("slug") or "").strip()

        parametres = urlencode(parcours.en_parametres())
        if not slug or not parcours.adresse:
            return redirect(f"{reverse('assistant:home')}?{parametres}")

        destination = reverse("assistant:produit", kwargs={"slug": slug})
        return redirect(f"{destination}?{parametres}")


class ProduitView(TurboFrameMixin, DetailView):
    model = ProduitPage
    template_name = "ui/pages/assistant/produit.html"
    context_object_name = "produit"

    def get_queryset(self):
        return ProduitPage.objects.live()


class SolutionsView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/solutions.html"


class LieuView(TurboFrameMixin, DetailView):
    model = DisplayedActeur
    template_name = "ui/pages/assistant/lieu.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "lieu"

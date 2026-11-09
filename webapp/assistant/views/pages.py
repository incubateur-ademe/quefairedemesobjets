from dataclasses import replace
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from assistant.consignes import block_for, consignes_for
from assistant.forms import SearchForm
from assistant.objets import synonyme_label
from assistant.parcours import Parcours
from assistant.solutions import (
    address_error,
    fiche_slug_for,
    groupes_in_order,
    label_of,
    nearest_lieux,
    position_of,
    requested_gestes,
)
from qfdmd.models import ProduitPage

from .mixins import TurboFrameMixin


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"
    form = None

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            parcours=Parcours.from_query(self.request.GET),
            erreurs=self.form.errors if self.form else None,
            **kwargs,
        )


class SearchView(View):
    """Routes the home form to the objet's fiche, or shows the home page again
    with its errors (a redirect would lose them)."""

    def get(self, request, *args, **kwargs):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HomeView.as_view(form=form)(request)

        fiche = form.cleaned_data["fiche"]
        parcours = replace(Parcours.from_query(request.GET), fiche="")
        destination = reverse("assistant:produit", kwargs={"slug": fiche.slug})
        return redirect(f"{destination}?{urlencode(parcours.as_params())}")


class ProduitView(TurboFrameMixin, DetailView):
    model = ProduitPage
    template_name = "ui/pages/assistant/produit.html"
    context_object_name = "produit"

    def get_queryset(self):
        return ProduitPage.objects.live()

    def get_context_data(self, **kwargs):
        # The search field shows the synonyme chosen, else the typed label,
        # else the fiche's title.
        parcours = Parcours.from_query(self.request.GET)
        synonyme = synonyme_label(parcours.synonyme, self.object)
        parcours = replace(
            parcours,
            fiche=self.object.slug,
            objet=synonyme or parcours.objet or self.object.title,
            synonyme=parcours.synonyme if synonyme else "",
        )
        return super().get_context_data(
            parcours=parcours,
            parametres=urlencode(parcours.as_params()),
            consignes=consignes_for(self.object, parcours),
            **kwargs,
        )


class SolutionsView(TurboFrameMixin, TemplateView):
    """Map screen: the map fetches its places itself, on load and on every
    move; the page only renders them for the accessible list."""

    template_name = "ui/pages/assistant/solutions.html"

    def get_context_data(self, **kwargs):
        parcours = Parcours.from_query(self.request.GET)
        if not parcours.fiche:
            parcours = replace(parcours, fiche=fiche_slug_for(parcours.objet))
        gestes = requested_gestes(self.request.GET)
        longitude, latitude = position_of(parcours)
        return super().get_context_data(
            parcours=parcours,
            gestes=gestes,
            libelle_geste=label_of(block_for(gestes), groupes_in_order(gestes)),
            url_fiche=self._fiche_url(parcours),
            longitude=longitude,
            latitude=latitude,
            erreur_adresse=address_error(parcours),
            adresse_precise=parcours.precise and parcours.is_located,
            lieux=nearest_lieux(gestes, parcours.fiche, longitude, latitude),
            **kwargs,
        )

    def _fiche_url(self, parcours: Parcours) -> str:
        """Back to the objet's fiche, or to the home page failing that."""
        if not parcours.fiche:
            return f"{reverse('assistant:home')}?{urlencode(parcours.as_params())}"
        destination = reverse("assistant:produit", kwargs={"slug": parcours.fiche})
        return f"{destination}?{urlencode(replace(parcours, fiche='').as_params())}"

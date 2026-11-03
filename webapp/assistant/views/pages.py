from dataclasses import replace
from urllib.parse import urlencode

from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from assistant.consignes import block_for, consignes_for
from assistant.forms import (
    MISSING_ADRESSE_MESSAGE,
    UNKNOWN_ADRESSE_MESSAGE,
    SearchForm,
)
from assistant.objets import fiche_for_label, synonyme_label
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage
from qfdmo.lieux_query import sous_categorie_ids_for
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction

from .mixins import TurboFrameMixin

PARIS = (2.3488, 48.8534)


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"

    def get(self, request, *args, form=None, **kwargs):
        """`form`: the refused search, shown again with its messages."""
        self.form = form
        return super().get(request, *args, **kwargs)

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
            return HomeView.as_view()(request, form=form)

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
            parcours = replace(parcours, fiche=_fiche_slug_for(parcours.objet))
        gestes = _requested_gestes(self.request.GET)
        groupes = _groupes_in_order(gestes)
        block = block_for(gestes)

        longitude, latitude = _position_of(parcours)
        return super().get_context_data(
            parcours=parcours,
            gestes=gestes,
            libelle_geste=_label_of(block, groupes),
            url_fiche=self._fiche_url(parcours),
            longitude=longitude,
            latitude=latitude,
            erreur_adresse=(
                ""
                if parcours.is_located
                else (
                    UNKNOWN_ADRESSE_MESSAGE
                    if parcours.adresse
                    else MISSING_ADRESSE_MESSAGE
                )
            ),
            adresse_precise=parcours.precise and parcours.is_located,
            lieux=_nearest_lieux(gestes, parcours.fiche, longitude, latitude),
            **kwargs,
        )

    def _fiche_url(self, parcours: Parcours) -> str:
        """Back to the objet's fiche, or to the home page failing that."""
        if not parcours.fiche:
            return f"{reverse('assistant:home')}?{urlencode(parcours.as_params())}"
        destination = reverse("assistant:produit", kwargs={"slug": parcours.fiche})
        return f"{destination}?{urlencode(replace(parcours, fiche='').as_params())}"


def _label_of(block, groupes) -> str:
    if block:
        return block["libelle"]
    if groupes:
        return groupes[0].libelle_court or groupes[0].libelle
    return ""


def _fiche_slug_for(label: str) -> str:
    """The fiche a label designates, for a shared URL carrying only the text."""
    fiche = fiche_for_label(label) if label else None
    return fiche.slug if fiche else ""


def _requested_gestes(query) -> list[str]:
    seen: list[str] = []
    for code in query.getlist("geste"):
        code = code.strip()
        if code and code not in seen:
            seen.append(code)
    return seen


def _groupes_in_order(codes: list[str]) -> list[GroupeAction]:
    by_code = {g.code: g for g in GroupeAction.objects.filter(code__in=codes)}
    return [by_code[code] for code in codes if code in by_code]


def _sous_categorie_ids_of(slug: str) -> list[int]:
    """An unknown fiche narrows nothing: the screen still shows its places."""
    try:
        return sous_categorie_ids_for(slug) if slug else []
    except Http404:
        return []


def _nearest_lieux(gestes, slug, longitude, latitude):
    if not gestes:
        return []
    return (
        DisplayedActeur.objects.all()
        .proposing(gestes, _sous_categorie_ids_of(slug))
        .nearest_to(longitude, latitude)
        .for_the_map()
    )


def _position_of(parcours: Parcours) -> tuple[float, float]:
    if parcours.is_located:
        return parcours.longitude, parcours.latitude
    return PARIS

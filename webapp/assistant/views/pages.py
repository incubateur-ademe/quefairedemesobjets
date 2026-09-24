from dataclasses import replace
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView

from assistant.consignes import block_for, consignes_for
from assistant.forms import SearchForm
from assistant.lieu import gestes_of, offers_bonus, practical_info_of
from assistant.objets import fiche_for_label
from assistant.parcours import Parcours
from qfdmd.models import ProduitPage
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction

from .mixins import TurboFrameMixin


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"

    def get(self, request, *args, form=None, **kwargs):
        """`form` is passed by `SearchView` when the input is refused: the home
        page then shows again with its messages."""
        self.form = form
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            parcours=Parcours.from_query(self.request.GET),
            erreurs=getattr(self, "form", None) and self.form.errors,
            **kwargs,
        )


class SearchView(View):
    """Receives the home form and routes to the objet's fiche.

    A redirect rather than a render: the final URL is the fiche's, hence
    shareable, reloadable and correct in the history.

    An incomplete input goes back to the home page with what was already
    typed, rather than showing an error on an emptied form.
    """

    def get(self, request, *args, **kwargs):
        form = SearchForm(request.GET)
        if not form.is_valid():
            # Show the home page again with its errors rather than redirecting
            # to it: a redirect would lose the messages and the user would see
            # a filled form that refuses to move on, without knowing why.
            return HomeView.as_view()(request, form=form)

        # The form yields the fiche itself: `get_absolute_url` does not exist
        # on this model, but the route derives directly from its slug.
        fiche = form.cleaned_data["fiche"]
        # The path carries the slug: the query string does not repeat it.
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
        # The fiche is the page itself: the links leaving it carry its slug.
        parcours = replace(
            Parcours.from_query(self.request.GET), fiche=self.object.slug
        )
        return super().get_context_data(
            parcours=parcours,
            parametres=urlencode(parcours.as_params()),
            consignes=consignes_for(self.object, parcours),
            **kwargs,
        )


class SolutionsView(TurboFrameMixin, TemplateView):
    """Map screen: the lieux offering the chosen geste, around the address.

    The map receives no lieux at render time: it requests them itself as
    GeoJSON once the canvas is ready, and requests them again on every move
    (#3356). Serving them here would freeze them at first display.
    """

    template_name = "ui/pages/assistant/solutions.html"

    def get_context_data(self, **kwargs):
        parcours = Parcours.from_query(self.request.GET)
        if not parcours.fiche:
            parcours = replace(parcours, fiche=_fiche_slug_for(parcours.objet))
        # A block of the fiche may span several gestes ("Donner ou revendre"):
        # `geste` is repeated in the query string, in the block's order.
        gestes = _requested_gestes(self.request.GET)
        groupes = _groupes_in_order(gestes)
        block = block_for(gestes)

        longitude, latitude = _position_of(parcours)
        return super().get_context_data(
            parcours=parcours,
            gestes=gestes,
            # The GeoJSON endpoint expects the fiche's slug, not the typed
            # label: the slug is what carries the sous-catégories.
            slug=parcours.fiche,
            libelle_geste=(
                block["libelle"]
                if block
                else (groupes[0].libelle_court or groupes[0].libelle) if groupes else ""
            ),
            # Several gestes share one map: the pins take the first one's color.
            couleur_geste=groupes[0].couleur if groupes else "",
            url_fiche=self._fiche_url(parcours),
            # A pin's link carries the parcours: without it, "Revenir aux
            # solutions" would lose the geste and the address.
            parametres_lieu=urlencode(
                {**parcours.as_params(), "geste": gestes}, doseq=True
            ),
            longitude=longitude,
            latitude=latitude,
            # The red marker only shows for a precise address (#3356).
            adresse_precise=parcours.precise and parcours.is_located,
            **kwargs,
        )

    def _fiche_url(self, parcours: Parcours) -> str:
        """Back to the objet's fiche, or to the home page failing that.

        The home page is only a last resort: a shared URL often carries only
        the label, and sending the user to the form would make them redo a
        search they just did.
        """
        if not parcours.fiche:
            return f"{reverse('assistant:home')}?{urlencode(parcours.as_params())}"
        destination = reverse("assistant:produit", kwargs={"slug": parcours.fiche})
        return f"{destination}?{urlencode(replace(parcours, fiche='').as_params())}"


# Default center: Paris, when the address has not been geocoded.
DEFAULT_CENTER = (2.3488, 48.8534)


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


def _position_of(parcours: Parcours) -> tuple[float, float]:
    if parcours.is_located:
        return parcours.longitude, parcours.latitude
    return DEFAULT_CENTER


class LieuView(TurboFrameMixin, DetailView):
    model = DisplayedActeur
    template_name = "ui/pages/assistant/lieu.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "lieu"

    def get_queryset(self):
        return DisplayedActeur.objects.all().for_the_detail()

    def get_context_data(self, **kwargs):
        parcours = Parcours.from_query(self.request.GET)
        # Going back to the solutions must recover the geste, which the
        # parcours does not carry: it is the choice made on the fiche.
        back = {**parcours.as_params()}
        if gestes := [v for v in self.request.GET.getlist("geste") if v.strip()]:
            back["geste"] = gestes
        return super().get_context_data(
            parcours=parcours,
            parametres=urlencode(back, doseq=True),
            infos_pratiques=practical_info_of(self.object),
            bonus_reparation=offers_bonus(self.object),
            gestes=gestes_of(self.object),
            **kwargs,
        )

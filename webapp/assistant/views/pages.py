from django.views.generic import DetailView, TemplateView

from qfdmd.models import ProduitPage
from qfdmo.models.acteur import DisplayedActeur

from .mixins import TurboFrameMixin


class HomeView(TurboFrameMixin, TemplateView):
    template_name = "ui/pages/assistant/home.html"


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

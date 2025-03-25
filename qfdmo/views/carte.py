from django.views.generic import DetailView

from qfdmo.models import CarteConfig


class CustomCarteView(DetailView):
    model = CarteConfig

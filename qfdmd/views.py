from django.views.generic import DetailView, View

from qfdmd.models import Synonyme


class HomeView(View):
    pass


class SynonymeDetailView(DetailView):
    model = Synonyme

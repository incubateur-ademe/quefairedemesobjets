import json

import requests
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Count, F
from django.shortcuts import render
from django.views.generic.edit import FormView

from qfdmo.forms import FooForm
from qfdmo.models import LVAOBase, ReemploiActeur

DEFAULT_LIMIT = 10
BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


class FooFormView(FormView):
    form_class = FooForm
    template_name = "qfdmo/homepage.html"

    def get_initial(self):
        initial = super().get_initial()
        # initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        initial["adresse"] = self.request.GET.get("adresse")
        return initial

    def get_context_data(self, **kwargs):
        kwargs["location"] = "{}"
        kwargs["reemploiacteurs"] = "{}"

        if adresse := self.request.GET.get("adresse", "").strip().replace(" ", "+"):
            response = requests.get(BAN_API_URL.format(adresse))
            data = response.json()
            if (
                response.status_code < 400
                and data["features"]
                and (geo := data["features"][0]["geometry"])
            ):
                kwargs["location"] = json.dumps(data["features"][0])

                reference_point = Point(
                    geo["coordinates"][0], geo["coordinates"][1], srid=4326
                )

                # Remplacez par le nombre d'acteurs que vous voulez obtenir
                kwargs["reemploi_acteurs"] = ReemploiActeur.objects.annotate(
                    distance=Distance("location", reference_point)
                ).order_by("distance")[:DEFAULT_LIMIT]

        return super().get_context_data(**kwargs)


# Create your views here.
def homepage(request):
    return render(
        request,
        "qfdmo/homepage.html",
    )


def analyse(request):
    lvao_bases = (
        LVAOBase.objects.all()
        .annotate(lvao_base_revision_count=Count("lvao_base_revisions"))
        .annotate(action_count=Count("lvao_base_revisions__actions", distinct=True))
        .filter(lvao_base_revision_count__gt=1)
        .exclude(lvao_base_revision_count=F("action_count"))
        .order_by("-lvao_base_revision_count")
    )

    return render(
        request,
        "qfdmo/analyse.html",
        {
            "lvao_bases": lvao_bases,
        },
    )


def analyse_lvao_base(request, id):
    lvao_base = LVAOBase.objects.get(id=id)
    lvao_base_revisions = lvao_base.lvao_base_revisions.prefetch_related(
        "actions",
        "sous_categories__categorie",
        "acteur_type",
        "acteur_services",
    ).all()
    reemploi_acteur = ReemploiActeur.objects.filter(
        identifiant_unique=lvao_base.identifiant_unique
    ).first()

    return render(
        request,
        "qfdmo/analyse_lvao_base.html",
        {
            "lvao_base": lvao_base,
            "lvao_base_revisions": lvao_base_revisions,
            "reemploi_acteur": reemploi_acteur,
        },
    )

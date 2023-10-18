import json
import threading

import unidecode
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance  # type: ignore
from django.core.management import call_command
from django.db.models import Min, QuerySet
from django.db.models.functions import Length, Lower
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET
from django.views.generic.edit import FormView

from core.jinja2_handler import get_action_list
from qfdmo.forms import GetReemploiSolutionForm
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    FinalActeur,
    FinalPropositionService,
    Objet,
    SousCategorieObjet,
)

DEFAULT_LIMIT = 10
BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"
DISTANCE_MAX = 30000


class ReemploiSolutionView(FormView):
    form_class = GetReemploiSolutionForm
    template_name = "qfdmo/reemploi_solution.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        initial["adresse"] = self.request.GET.get("adresse")
        initial["direction"] = self.request.GET.get(
            "direction", settings.DEFAULT_ACTION_DIRECTION
        )
        initial["action_list"] = self.request.GET.get("action_list")
        initial["latitude"] = self.request.GET.get("latitude")
        initial["longitude"] = self.request.GET.get("longitude")
        initial["digital"] = self.request.GET.get("digital")
        return initial

    def get_context_data(self, **kwargs):
        kwargs["location"] = "{}"
        kwargs["acteurs"] = FinalActeur.objects.none()

        sous_categories_objets: QuerySet | None = None
        if objet_q := self.request.GET.get("sous_categorie_objet", None):
            sous_categories_objets = SousCategorieObjet.objects.filter(
                objets__nom=objet_q
            )
        action_selection = get_action_list(self.request)
        if sous_categories_objets:
            acteurs = FinalActeur.objects.filter(
                proposition_services__in=FinalPropositionService.objects.filter(
                    action__in=action_selection,
                    sous_categories__in=sous_categories_objets,
                ),
                statut=ActeurStatus.ACTIF,
            )
        else:
            acteurs = FinalActeur.objects.filter(
                proposition_services__action__in=action_selection,
                statut=ActeurStatus.ACTIF,
            )
        acteurs = acteurs.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action",
            "proposition_services__action__directions",
            "proposition_services__acteur_service",
            "acteur_type",
        ).distinct()

        if sous_categories_objets:
            acteurs = acteurs.filter(
                proposition_services__sous_categories__in=sous_categories_objets
            )
        kwargs["acteurs_digitaux"] = (
            acteurs.filter(acteur_type__nom="acteur digital")
            .annotate(min_action_order=Min("proposition_services__action__order"))
            .order_by("min_action_order", "?")
        )
        kwargs["nb_acteurs_digitaux"] = acteurs.filter(
            acteur_type__nom="acteur digital"
        ).count()

        if (latitude := self.request.GET.get("latitude", None)) and (
            longitude := self.request.GET.get("longitude", None)
        ):
            kwargs["location"] = json.dumps(
                {"latitude": latitude, "longitude": longitude}
            )
            reference_point = Point(float(longitude), float(latitude), srid=4326)
            # FIXME : add a test to check distinct point
            acteurs_physique = acteurs.annotate(
                distance=Distance("location", reference_point)
            ).exclude(acteur_type__nom="acteur digital")

            kwargs["acteurs"] = acteurs_physique.filter(
                distance__lte=DISTANCE_MAX
            ).order_by("distance")[:DEFAULT_LIMIT]

        return super().get_context_data(**kwargs)


def getorcreate_revision_acteur(request, acteur_id):
    acteur = Acteur.objects.get(id=acteur_id)
    revision_acteur = acteur.get_or_create_revision()
    return redirect("admin:qfdmo_revisionacteur_change", revision_acteur.id)


class RefreshMateriazedViewThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        call_command("refresh_materialized_view")


def refresh_acteur_view(request):
    RefreshMateriazedViewThread().start()
    return redirect(request.META["HTTP_REFERER"])


@require_GET
def get_object_list(request):
    query = unidecode.unidecode(request.GET.get("q"))
    objets = (
        Objet.objects.annotate(
            nom_unaccent=Unaccent(Lower("nom")),
        )
        .annotate(
            distance=TrigramWordDistance(query, "nom_unaccent"),
            length=Length("nom"),
        )
        .order_by("distance", "length")[:10]
    )
    return JsonResponse([objet.nom for objet in objets], safe=False)

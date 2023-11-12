import json

import unidecode
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance  # type: ignore
from django.db.models import Min, Q
from django.db.models.functions import Length, Lower
from django.forms.forms import BaseForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.generic.edit import FormView

from core.jinja2_handler import get_action_list
from qfdmo.forms import GetReemploiSolutionForm
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    ActeurType,
    FinalActeur,
    FinalPropositionService,
    Objet,
    RevisionActeur,
)
from qfdmo.models.action import CachedDirectionAction
from qfdmo.thread.materialized_view import RefreshMateriazedViewThread

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


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
        initial["label_reparacteur"] = self.request.GET.get("label_reparacteur")
        initial["ss_cat"] = (
            self.request.GET.get("ss_cat") if initial["sous_categorie_objet"] else None
        )

        return initial

    def get_form(self, form_class: type | None = GetReemploiSolutionForm) -> BaseForm:
        my_form = super().get_form(form_class)
        # Here we need to load choices after initialisation because of async management
        # in prod + cache
        my_form.load_choices()
        return my_form

    def get_context_data(self, **kwargs):
        kwargs["location"] = "{}"
        kwargs["acteurs"] = FinalActeur.objects.none()

        sous_categorie_id = (
            int(self.request.GET.get("ss_cat", 0))
            if self.request.GET.get("sous_categorie_objet")
            else None
        )
        action_selection_ids = [a["id"] for a in get_action_list(self.request)]

        ps_filter = self._build_ps_filter(action_selection_ids, sous_categorie_id)

        acteurs = FinalActeur.objects.filter(ps_filter)

        acteurs = acteurs.prefetch_related(
            "proposition_services__sous_categories",
            "proposition_services__sous_categories__categorie",
            "proposition_services__action",
            "proposition_services__acteur_service",
        ).distinct()

        if sous_categorie_id:
            acteurs = acteurs.filter(
                proposition_services__sous_categories__id=sous_categorie_id
            )

        if self.request.GET.get("digital") and int(self.request.GET.get("digital")):
            acteurs = (
                acteurs.filter(acteur_type_id=ActeurType.get_digital_acteur_type_id())
                .annotate(min_action_order=Min("proposition_services__action__order"))
                .order_by("min_action_order", "?")
            )
            kwargs["acteurs"] = acteurs
        else:
            if (latitude := self.request.GET.get("latitude", None)) and (
                longitude := self.request.GET.get("longitude", None)
            ):
                kwargs["location"] = json.dumps(
                    {"latitude": latitude, "longitude": longitude}
                )
                reference_point = Point(float(longitude), float(latitude), srid=4326)
                distance_in_degrees = settings.DISTANCE_MAX / 111320

                # FIXME : add a test to check distinct point
                acteurs_physique = acteurs.annotate(
                    distance=Distance("location", reference_point)
                ).exclude(acteur_type_id=ActeurType.get_digital_acteur_type_id())

                # FIXME : ecrire quelques part qu'il faut utiliser dwithin
                # pour utiliser l'index
                acteurs = acteurs_physique.filter(
                    location__dwithin=(
                        reference_point,
                        distance_in_degrees,
                    )
                ).order_by("distance")[: settings.MAX_SOLUTION_DISPLAYED_ON_MAP]
                kwargs["acteurs"] = acteurs
        return super().get_context_data(**kwargs)

    def _build_ps_filter(self, action_selection_ids, sous_categorie_id: int | None):
        reparer_action_id = None
        if (
            self.request.GET.get("label_reparacteur")
            and CachedDirectionAction.get_reparer_action_id() in action_selection_ids
        ):
            reparer_action_id = CachedDirectionAction.get_reparer_action_id()
            action_selection_ids = [
                a for a in action_selection_ids if a != reparer_action_id
            ]

        ps_filter = Q()
        if sous_categorie_id:
            if action_selection_ids:
                ps_filter = ps_filter | Q(
                    proposition_services__in=FinalPropositionService.objects.filter(
                        action_id__in=action_selection_ids,
                        sous_categories__id=sous_categorie_id,
                    ),
                    statut=ActeurStatus.ACTIF,
                )
            if reparer_action_id:
                ps_filter = ps_filter | Q(
                    proposition_services__in=FinalPropositionService.objects.filter(
                        action_id=reparer_action_id,
                        sous_categories__id=sous_categorie_id,
                    ),
                    label_reparacteur=True,
                    statut=ActeurStatus.ACTIF,
                )
        else:
            if action_selection_ids:
                ps_filter = ps_filter | Q(
                    proposition_services__action_id__in=action_selection_ids,
                    statut=ActeurStatus.ACTIF,
                )
            if reparer_action_id:
                ps_filter = ps_filter | Q(
                    proposition_services__action_id=reparer_action_id,
                    label_reparacteur=True,
                    statut=ActeurStatus.ACTIF,
                )
        return ps_filter


def getorcreate_revision_acteur(request, acteur_identifiant):
    acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
    revision_acteur = acteur.get_or_create_revision()
    return redirect(
        "admin:qfdmo_revisionacteur_change", quote(revision_acteur.identifiant_unique)
    )


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
        .prefetch_related("sous_categorie")
        .annotate(
            distance=TrigramWordDistance(query, "nom_unaccent"),
            length=Length("nom"),
        )
        .order_by("distance", "length")[:10]
    )
    return JsonResponse(
        [
            {
                "label": objet.nom,
                "sub_label": objet.sous_categorie.nom,
                "identifier": objet.sous_categorie_id,
            }
            for objet in objets
        ],
        safe=False,
    )


# FIXME : should be tested
def solution_detail(request, identifiant_unique):
    final_acteur = FinalActeur.objects.get(identifiant_unique=identifiant_unique)
    return render(request, "qfdmo/solution_detail.html", {"final_acteur": final_acteur})


# FIXME : should be tested
def solution_admin(request, identifiant_unique):
    acteur = RevisionActeur.objects.filter(
        identifiant_unique=identifiant_unique
    ).first()

    if acteur:
        return redirect(
            "admin:qfdmo_revisionacteur_change", quote(acteur.identifiant_unique)
        )
    acteur = Acteur.objects.get(identifiant_unique=identifiant_unique)
    return redirect("admin:qfdmo_acteur_change", quote(acteur.identifiant_unique))

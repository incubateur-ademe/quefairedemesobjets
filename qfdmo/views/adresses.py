import json

import unidecode
from django.conf import settings
from django.contrib.admin.utils import quote
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, Polygon
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
from core.utils import get_direction
from qfdmo.forms import CarteAddressesForm, IframeAddressesForm
from qfdmo.models import (
    Acteur,
    ActeurStatus,
    ActeurType,
    CachedDirectionAction,
    DisplayedActeur,
    DisplayedPropositionService,
    Objet,
    RevisionActeur,
)
from qfdmo.thread.materialized_view import RefreshMateriazedViewThread

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


class AddressesView(FormView):
    form_class = IframeAddressesForm
    template_name = "qfdmo/adresses.html"

    def get_form_class(self) -> type:
        if self.request.GET.get("carte") is not None:
            return CarteAddressesForm
        return super().get_form_class()

    def _get_search_in_zone_params(self):
        center = []
        my_bbox_polygon = []
        if search_in_zone := self.request.GET.get("search_in_zone"):
            search_in_zone = json.loads(search_in_zone)
            if (
                "center" in search_in_zone
                and "lat" in search_in_zone["center"]
                and "lng" in search_in_zone["center"]
            ):
                center = [
                    search_in_zone["center"]["lng"],
                    search_in_zone["center"]["lat"],
                ]

            if (
                "southWest" in search_in_zone
                and "lat" in search_in_zone["southWest"]
                and "lng" in search_in_zone["southWest"]
                and "northEast" in search_in_zone
                and "lat" in search_in_zone["northEast"]
                and "lng" in search_in_zone["northEast"]
            ):
                my_bbox_polygon = [
                    search_in_zone["southWest"]["lng"],
                    search_in_zone["southWest"]["lat"],
                    search_in_zone["northEast"]["lng"],
                    search_in_zone["northEast"]["lat"],
                ]  # [xmin, ymin, xmax, ymax]
        return center, my_bbox_polygon

    def get_initial(self):
        initial = super().get_initial()
        initial["sous_categorie_objet"] = self.request.GET.get("sous_categorie_objet")
        initial["adresse"] = self.request.GET.get("adresse")
        initial["digital"] = self.request.GET.get("digital", "0")
        initial["direction"] = get_direction(self.request)
        initial["action_list"] = self.request.GET.get("action_list")
        initial["latitude"] = self.request.GET.get("latitude")
        initial["longitude"] = self.request.GET.get("longitude")
        initial["label_reparacteur"] = self.request.GET.get("label_reparacteur")
        initial["sc_id"] = (
            self.request.GET.get("sc_id") if initial["sous_categorie_objet"] else None
        )

        return initial

    def get_form(self, form_class: type | None = None) -> BaseForm:
        if form_class is None:
            form_class = self.get_form_class()
        my_form = super().get_form(form_class)
        # Here we need to load choices after initialisation because of async management
        # in prod + cache
        my_form.load_choices(first_direction=self.request.GET.get("first_dir"))
        return my_form

    def get_context_data(self, **kwargs):
        kwargs["location"] = "{}"
        kwargs["acteurs"] = DisplayedActeur.objects.none()

        sous_categorie_id = None
        if (
            self.request.GET.get("sous_categorie_objet")
            and self.request.GET.get("sc_id", "").isnumeric()
        ):
            sous_categorie_id = int(self.request.GET.get("sc_id", "0"))

        action_selection_ids = [a["id"] for a in get_action_list(self.request)]

        ps_filter = self._build_ps_filter(action_selection_ids, sous_categorie_id)

        acteurs = DisplayedActeur.objects.filter(ps_filter)

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

        if self.request.GET.get("digital") and self.request.GET.get("digital") == "1":
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

                center, my_bbox_polygon = self._get_search_in_zone_params()
                if center:
                    longitude = center[0]
                    latitude = center[1]

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
                ).order_by("distance")
                bbox_acteurs = None
                if my_bbox_polygon:
                    bbox_acteurs = acteurs.filter(
                        location__within=Polygon.from_bbox(my_bbox_polygon)
                    )[: settings.MAX_SOLUTION_DISPLAYED_ON_MAP]
                    if bbox_acteurs:
                        kwargs["bbox"] = my_bbox_polygon

                kwargs["acteurs"] = (
                    bbox_acteurs or acteurs[: settings.MAX_SOLUTION_DISPLAYED_ON_MAP]
                )

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
                    proposition_services__in=DisplayedPropositionService.objects.filter(
                        action_id__in=action_selection_ids,
                        sous_categories__id=sous_categorie_id,
                    ),
                    statut=ActeurStatus.ACTIF,
                )
            if reparer_action_id:
                ps_filter = ps_filter | Q(
                    proposition_services__in=DisplayedPropositionService.objects.filter(
                        action_id=reparer_action_id,
                        sous_categories__id=sous_categorie_id,
                    ),
                    labels__code="reparacteur",
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
                    labels__code="reparacteur",
                    statut=ActeurStatus.ACTIF,
                )
        return ps_filter


# TODO : should be deprecated once all is moved to the displayed acteur
def getorcreate_revisionacteur(request, acteur_identifiant):
    acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
    revision_acteur = acteur.get_or_create_revision()
    return redirect(
        "admin:qfdmo_revisionacteur_change", quote(revision_acteur.identifiant_unique)
    )


def getorcreate_correctionequipeacteur(request, acteur_identifiant):
    acteur = Acteur.objects.get(identifiant_unique=acteur_identifiant)
    revision_acteur = acteur.get_or_create_correctionequipe()
    return redirect(
        "admin:qfdmo_revisionacteur_change", quote(revision_acteur.identifiant_unique)
    )


def refresh_acteur_view(request):
    RefreshMateriazedViewThread().start()
    return redirect("admin:index")


@require_GET
def get_object_list(request):
    query = unidecode.unidecode(request.GET.get("q"))
    objets = (
        Objet.objects.annotate(
            libelle_unaccent=Unaccent(Lower("libelle")),
        )
        .prefetch_related("sous_categorie")
        .annotate(
            distance=TrigramWordDistance(query, "libelle_unaccent"),
            length=Length("libelle"),
        )
        .order_by("distance", "length")[:10]
    )
    object_list = [
        {
            "label": objet.libelle,
            "sub_label": objet.sous_categorie.libelle,
            "identifier": objet.sous_categorie_id,
        }
        for objet in objets
    ]

    return JsonResponse(
        object_list,
        safe=False,
    )


def adresse_detail(request, identifiant_unique):
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    direction = request.GET.get("direction")
    displayed_acteur = DisplayedActeur.objects.get(
        identifiant_unique=identifiant_unique
    )
    return render(
        request,
        "qfdmo/adresse_detail.html",
        {
            "adresse": displayed_acteur,
            "latitude": latitude,
            "longitude": longitude,
            "direction": direction,
        },
    )


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

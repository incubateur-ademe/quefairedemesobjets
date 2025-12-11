import json
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, View

from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import SuggestionGroupe, SuggestionStatut

logger = logging.getLogger(__name__)


class SuggestionGroupeStatusView(LoginRequiredMixin, FormView):
    form_class = SuggestionGroupeStatusForm

    def get_success_url(self):
        return reverse_lazy(
            "data:suggestion_groupe",
            kwargs={"suggestion_groupe_id": self.kwargs["suggestion_groupe_id"]},
        )

    def form_valid(self, form):
        suggestion_groupe = get_object_or_404(
            SuggestionGroupe.objects,
            id=self.kwargs["suggestion_groupe_id"],
        )
        action = form.cleaned_data["action"]
        if action == "validate":
            suggestion_groupe.statut = SuggestionStatut.ATRAITER
        elif action == "reject":
            suggestion_groupe.statut = SuggestionStatut.REJETEE
        elif action == "to_process":
            suggestion_groupe.statut = SuggestionStatut.AVALIDER
        suggestion_groupe.save()

        return super().form_valid(form)


class SuggestionGroupeView(LoginRequiredMixin, View):
    template_name = "data/_partials/suggestion_groupe_refresh_stream.html"

    def _manage_tab_in_context(self, context, request, suggestion_groupe):

        def _append_location_to_points(
            points, latitude_data, longitude_data, key, color, draggable
        ):
            points.append(
                {
                    "latitude": float(latitude_data[key]),
                    "longitude": float(longitude_data[key]),
                    "color": color,
                    "draggable": draggable,
                }
            )

        context["tab"] = request.GET.get("tab", request.POST.get("tab", None))
        if context["tab"] == "acteur":
            context["uuid"] = suggestion_groupe.displayed_acteur_uuid()
        if context["tab"] == "localisation":
            if (
                "latitude" in context["fields_values"]
                and "longitude" in context["fields_values"]
            ):
                latitude_data = context["fields_values"]["latitude"]
                longitude_data = context["fields_values"]["longitude"]

                # Prepare point list to display in map
                points = []

                # Point pour old_value (rouge, non draggable)
                if latitude_data.get("old_value") and longitude_data.get("old_value"):
                    points.append(
                        {
                            "latitude": float(latitude_data["old_value"]),
                            "longitude": float(longitude_data["old_value"]),
                            "color": "red",
                            "draggable": False,
                        }
                    )

                # Point pour new_value (vert #26A69A, non draggable)
                if latitude_data.get("new_value") and longitude_data.get("new_value"):
                    points.append(
                        {
                            "latitude": float(latitude_data["new_value"]),
                            "longitude": float(longitude_data["new_value"]),
                            "color": "blue",
                            "draggable": False,
                        }
                    )

                if latitude_data.get("updated_displayed_value") and longitude_data.get(
                    "updated_displayed_value"
                ):
                    points.append(
                        {
                            "latitude": float(latitude_data["updated_displayed_value"]),
                            "longitude": float(
                                longitude_data["updated_displayed_value"]
                            ),
                            "color": "green",
                            "draggable": True,
                        }
                    )
                elif latitude_data.get("displayed_value") and longitude_data.get(
                    "displayed_value"
                ):
                    _append_location_to_points(
                        points,
                        latitude_data,
                        longitude_data,
                        "displayed_value",
                        "#00695C",
                        True,
                    )
                context["localisation"] = {
                    "points": points,
                }

        return context

    def get(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)

        context = suggestion_groupe.serialize().to_dict()
        context = self._manage_tab_in_context(context, request, suggestion_groupe)

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )

    def post(self, request, suggestion_groupe_id):
        suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)

        fields_values_payload = request.POST.get("fields_values", "{}")
        fields_groups_payload = request.POST.get("fields_groups", "{}")
        try:
            fields_values = (
                json.loads(fields_values_payload) if fields_values_payload else {}
            )
            fields_groups = (
                json.loads(fields_groups_payload) if fields_groups_payload else []
            )
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Payload fields_list invalide")
        _, errors = suggestion_groupe.update_from_serialized_data(
            fields_values, fields_groups
        )
        context = suggestion_groupe.serialize().to_dict()
        context["errors"] = errors
        context = self._manage_tab_in_context(context, request, suggestion_groupe)

        return render(
            request,
            self.template_name,
            context,
            content_type="text/vnd.turbo-stream.html",
        )


class GoogleStreetViewProxyView(LoginRequiredMixin, View):
    """Vue proxy pour Google Street View qui masque la clé API."""

    def get(self, request):
        """Redirige vers l'URL Google Street View avec la clé API côté serveur."""
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")
        heading = request.GET.get("heading", "210")
        pitch = request.GET.get("pitch", "10")
        fov = request.GET.get("fov", "80")

        if not latitude or not longitude:
            return HttpResponseBadRequest("Le paramètre 'location' est requis")

        if not settings.GOOGLE_MAPS_API_KEY:
            logger.error("GOOGLE_MAPS_API_KEY n'est pas configurée dans les settings")
            return HttpResponseBadRequest("La clé API Google Maps n'est pas configurée")

        # Valider et formater le paramètre location
        # Google Maps attend le format "lat,lng" (virgule non encodée)
        # Si location contient une virgule, valider les coordonnées

        latitude = float(latitude.replace(",", ".").strip())
        longitude = float(longitude.replace(",", ".").strip())

        # Construire l'URL Google Street View avec la clé API
        # Pour le paramètre location, on ne veut pas encoder la virgule
        # On construit donc l'URL manuellement pour ce paramètre
        base_url = "https://www.google.com/maps/embed/v1/streetview"
        other_params = {
            "key": str(settings.GOOGLE_MAPS_API_KEY),
            "heading": str(heading),
            "pitch": str(pitch),
            "fov": str(fov),
        }
        # Encoder les autres paramètres
        query_string = urlencode(other_params)
        # Ajouter location sans encoder la virgule
        streetview_url = f"{base_url}?{query_string}&location={latitude},{longitude}"

        # Logger l'URL sans exposer la clé API
        safe_url = streetview_url.replace(str(settings.GOOGLE_MAPS_API_KEY), "***")
        logger.debug(f"URL Street View générée: {safe_url}")

        # Rediriger vers l'URL Google Street View
        return redirect(streetview_url)

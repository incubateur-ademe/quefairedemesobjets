import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from data.models.suggestion import SuggestionGroupe, SuggestionStatut


class SuggestionGroupeStatusView(LoginRequiredMixin, View):
    def get(self, request, suggestion_groupe_id, action):
        suggestion_groupe = get_object_or_404(
            SuggestionGroupe.objects,
            id=suggestion_groupe_id,
        )

        if action == "validate":
            suggestion_groupe.statut = SuggestionStatut.ATRAITER
        elif action == "reject":
            suggestion_groupe.statut = SuggestionStatut.REJETEE
        elif action == "to_process":
            suggestion_groupe.statut = SuggestionStatut.AVALIDER
        else:
            return HttpResponseBadRequest(f"Action invalide: {action}")

        suggestion_groupe.save()

        return render(
            request,
            "data/_partials/suggestion_groupe_details.html",
            suggestion_groupe.serialize().to_dict(),
        )


class SuggestionGroupeView(LoginRequiredMixin, View):
    template_name = "data/_partials/suggestion_groupe_details.html"

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
            context["uuid"] = suggestion_groupe.displayed_acteur_uuid
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

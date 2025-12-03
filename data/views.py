import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.edit import FormView

from data.forms import SuggestionGroupeStatusForm
from data.models.suggestion import SuggestionGroupe, SuggestionStatut


class SuggestionGroupeStatusView(LoginRequiredMixin, FormView):
    form_class = SuggestionGroupeStatusForm

    def get_success_url(self):
        return reverse_lazy(
            "data:suggestion_groupe_details",
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


@login_required
@require_GET
def suggestion_groupe_details(request, suggestion_groupe_id):
    suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)
    context = suggestion_groupe.serialize().to_dict()
    context["tab"] = request.GET.get("tab", "")
    if context["tab"] == "acteur":
        context["uuid"] = suggestion_groupe.displayed_acteur_uuid()
    return render(
        request,
        "data/_partials/suggestion_groupe_refresh_stream.html",
        context,
        content_type="text/vnd.turbo-stream.html",
    )


@login_required
@require_POST
def update_suggestion_groupe_details(request, suggestion_groupe_id):
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

    # TODO : here we interpret the fields_listand create the needed suggestions

    suggestion_groupe.update_from_serialized_data(fields_values, fields_groups)

    context = suggestion_groupe.serialize().to_dict()

    # TODO : should be removed, only for tests
    context["requested_fields_list"] = suggestion_groupe.serialize().fields_values

    return render(
        request,
        "data/_partials/suggestion_groupe_refresh_stream.html",
        context,
        content_type="text/vnd.turbo-stream.html",
    )

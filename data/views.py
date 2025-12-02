import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView

from data.forms import SuggestionGroupeForm, SuggestionGroupeStatusForm
from data.models.suggestion import (
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)


class SuggestionGroupeMixin(FormView):
    template_name = "data/_partials/suggestion_groupe_row_type_source.html"

    def get_object(self):
        return get_object_or_404(
            SuggestionGroupe.objects.prefetch_related(
                "suggestion_unitaires",
                "acteur",
                "revision_acteur",
                "revision_acteur__parent",
            ),
            id=self.kwargs["suggestion_groupe_id"],
        )

    def get_success_url(self):
        return reverse_lazy(
            "data:suggestion_groupe",
            kwargs={"suggestion_groupe_id": self.kwargs["suggestion_groupe_id"]},
        )


class SuggestionGroupeView(LoginRequiredMixin, SuggestionGroupeMixin, FormView):
    form_class = SuggestionGroupeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suggestion_groupe = self.get_object()
        context["suggestion_groupe"] = suggestion_groupe
        context["suggestion_unitaires_by_champs"] = (
            suggestion_groupe.get_suggestion_unitaires_by_champs()
        )
        return context

    def form_valid(self, form):
        suggestion_groupe = self.get_object()
        champs = [champ.strip() for champ in form.cleaned_data["champs"].split("|")]
        valeurs = [value.strip() for value in form.cleaned_data["valeurs"].split("|")]

        suggestion_unitaire_to_remove = all(valeur in ["", "-"] for valeur in valeurs)

        suggestion_unitaires = suggestion_groupe.suggestion_unitaires.filter(
            champs=champs,
            suggestion_modele=form.cleaned_data["suggestion_modele"],
        )
        if suggestion_unitaires.count() > 1:
            raise Exception(
                "Plusieurs suggestions unitaires trouvées pour le même groupe de champs"
            )
        suggestion_unitaire = suggestion_unitaires.first()
        if suggestion_unitaire_to_remove:
            if suggestion_unitaire is not None:
                suggestion_unitaire.delete()
            return super().form_valid(form)
        if suggestion_unitaire is not None:
            suggestion_unitaire.valeurs = valeurs
            suggestion_unitaire.save()
            return super().form_valid(form)

        SuggestionUnitaire.objects.create(
            suggestion_groupe=suggestion_groupe,
            champs=champs,
            suggestion_modele=form.cleaned_data["suggestion_modele"],
            valeurs=valeurs,
        )
        return super().form_valid(form)


class SuggestionGroupeStatusView(LoginRequiredMixin, SuggestionGroupeMixin, FormView):
    form_class = SuggestionGroupeStatusForm

    def form_valid(self, form):
        suggestion_groupe = self.get_object()
        action = form.cleaned_data["action"]
        if action == "validate":
            suggestion_groupe.statut = SuggestionStatut.ATRAITER
        elif action == "reject":
            suggestion_groupe.statut = SuggestionStatut.REJETEE
        suggestion_groupe.save()
        return super().form_valid(form)


def get_suggestion_groupe_usefull_links(request, suggestion_groupe_id, usefull_link):
    suggestion_groupe = get_object_or_404(SuggestionGroupe, id=suggestion_groupe_id)
    acteur = suggestion_groupe.acteur
    revision_acteur = suggestion_groupe.revision_acteur
    if revision_acteur:
        parent_acteur = revision_acteur.parent
    else:
        parent_acteur = None

    latitude = (
        parent_acteur.latitude
        if parent_acteur
        else (
            revision_acteur.latitude
            if revision_acteur and revision_acteur.latitude
            else acteur.latitude
        )
    )
    longitude = (
        parent_acteur.longitude
        if parent_acteur
        else (
            revision_acteur.longitude
            if revision_acteur and revision_acteur.longitude
            else acteur.longitude
        )
    )
    google_maps_url = f"https://maps.google.com/maps?q={latitude},{longitude}&z=14&output=embed&output=embed"

    return render(
        request,
        "data/_partials/suggestion_groupe_usefull_links.html",
        {
            "suggestion_groupe": suggestion_groupe,
            "acteur": acteur,
            "revision_acteur": revision_acteur,
            "parent_acteur": parent_acteur,
            "google_maps_url": google_maps_url,
            "latitude": latitude,
            "longitude": longitude,
            "localisation": usefull_link == "localisation",
            "displayedacteur": usefull_link == "displayedacteur",
            "annuaire_entreprise": usefull_link == "annuaire_entreprise",
        },
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
            json.loads(fields_groups_payload) if fields_groups_payload else {}
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

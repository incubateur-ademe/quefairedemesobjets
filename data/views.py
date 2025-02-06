"""
DEPRECATED: cette vue sera bentôt caduque, on utilisera l'administration django
"""

from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.edit import FormView

from core.views import IsStaffMixin
from data.forms import SuggestionCohorteForm
from data.models import SuggestionAction, SuggestionStatut

ACTION_TO_VERB = {
    SuggestionAction.SOURCE_AJOUT: "ajoutera",
    SuggestionAction.SOURCE_SUPPRESSION: "supprimera",
    SuggestionAction.SOURCE_MODIFICATION: "modifiera",
}


class SuggestionManagement(IsStaffMixin, FormView):
    form_class = SuggestionCohorteForm
    template_name = "data/dags_validations.html"
    # success_url = "/data/suggestions"

    def get_success_url(self) -> str:
        return reverse("data:suggestions")

    def form_valid(self, form):
        # MANAGE search and display suggestion_cohorte details
        suggestion_cohorte = form.cleaned_data["suggestion_cohorte"]
        if self.request.POST.get("search"):
            context = {"form": form}
            context["suggestion_cohorte_instance"] = suggestion_cohorte
            suggestion_unitaires = suggestion_cohorte.suggestion_unitaires.all()
            context["metadata"] = {
                "nb_suggestions": suggestion_unitaires.count(),
                "description": (
                    "La validation de cette cohorte de suggestion "
                    f"{ACTION_TO_VERB[suggestion_cohorte.type_action]} l'ensemble des "
                    "acteurs"
                ),
                "source": suggestion_cohorte.identifiant_action,
            }
            suggestion_unitaires = suggestion_unitaires.order_by("?")[:100]
            context["suggestion_unitaires"] = suggestion_unitaires
            return render(self.request, self.template_name, context)
        # ELSE: update the status of the suggestion_cohorte and its
        # suggestion_cohortelines
        suggestion_cohorte = form.cleaned_data["suggestion_cohorte"]
        new_status = (
            SuggestionStatut.ATRAITER.value
            if self.request.POST.get("dag_valid") == "1"
            else SuggestionStatut.REJETEE.value
        )

        suggestion_cohorte.suggestion_unitaires.all().update(statut=new_status)
        suggestion_cohorte.statut = new_status
        suggestion_cohorte.save()

        messages.success(
            self.request,
            f"La cohorte {suggestion_cohorte} a été mise à jour avec le "
            f"statut {new_status}",
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Il y a des erreurs dans le formulaire.")
        return super().form_invalid(form)

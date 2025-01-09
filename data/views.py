from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import FormView

from data.forms import SuggestionCohorteForm
from data.models import SuggestionAction, SuggestionStatut


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


ACTION_TO_VERB = {
    SuggestionAction.SOURCE_AJOUT: "ajoutera",
    SuggestionAction.SOURCE_SUPPRESSION: "supprimera",
    SuggestionAction.SOURCE_MISESAJOUR: "mettra à jour",
}


class DagsValidation(IsStaffMixin, FormView):
    form_class = SuggestionCohorteForm
    template_name = "data/dags_validations.html"
    success_url = "/dags/validations"

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
            else SuggestionStatut.REJETER.value
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


# class DagsValidationDeprecated(IsStaffMixin, FormView):
#     form_class = SuggestionCohorteForm
#     template_name = "qfdmo/dags_validations.html"
#     success_url = "/dags/validations"

#     def get_initial(self):
#         initial = super().get_initial()
#         initial["suggestion_cohorte"] = self.request.GET.get("suggestion_cohorte")
#         return initial

#     def post(self, request, *args, **kwargs):

#         dag_valid = request.POST.get("dag_valid")
#         if dag_valid in ["1", "0"]:
#             return self.form_valid(self.get_form())
#         else:
#             suggestion_cohorte_obj = SuggestionCohorte.objects.get(
#                 pk=request.POST.get("suggestion_cohorte")
#             )
#             id = request.POST.get("id")
#             suggestion_unitaire = suggestion_cohorte_obj.suggestion_unitaires.filter(
#                 id=id
#             ).first()
#             identifiant_unique = request.POST.get("identifiant_unique")
#             index = request.POST.get("index")
#             action = request.POST.get("action")

#             if action == "validate":
#                 suggestion_unitaire.update_row_update_candidate(
#                     SuggestionStatut.ATRAITER.value, index
#                 )
#             elif action == "reject":
#                 suggestion_unitaire.update_row_update_candidate(
#                     SuggestionStatut.REJETER.value, index
#                 )

#             updated_candidat = suggestion_unitaire.get_candidat(index)

#             return render(
#                 request,
#                 "qfdmo/partials/candidat_row.html",
#                 {
#                     "identifiant_unique": identifiant_unique,
#                     "candidat": updated_candidat,
#                     "index": index,
#                     "request": request,
#                     "suggestion_cohorte": request.POST.get("suggestion_cohorte"),
#                     "suggestion_unitaire": suggestion_unitaire,
#                 },
#             )

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.request.GET.get("suggestion_cohorte"):
#             suggestion_cohorte = SuggestionCohorte.objects.get(
#                 pk=self.request.GET.get("suggestion_cohorte")
#             )
#             context["suggestion_cohorte_instance"] = suggestion_cohorte
#             suggestion_unitaires = (
#                 suggestion_cohorte.suggestion_unitaires.all().order_by("?")[:100]
#             )
#             context["suggestion_unitaires"] = suggestion_unitaires

#             if (
#                 suggestion_unitaires
#                 and suggestion_unitaires[0].change_type == "UPDATE_ACTOR"
#             ):
#                 # Pagination
#                 suggestion_unitaires = (
#                     suggestion_cohorte.suggestion_unitaires.all().order_by("id")
#                 )
#                 paginator = Paginator(suggestion_unitaires, 100)
#                 page_number = self.request.GET.get("page")
#                 page_obj = paginator.get_page(page_number)
#                 context["suggestion_unitaires"] = page_obj

#         return context

#     def form_valid(self, form):
#         if not form.is_valid():
#             raise ValueError("Form is not valid")
#         suggestion_cohorte_id = form.cleaned_data["suggestion_cohorte"].id
#         suggestion_cohorte_obj = (
#             SuggestionCohorte.objects.get(pk=suggestion_cohorte_id)
#         )
#         new_status = (
#             SuggestionStatut.ATRAITER.value
#             if self.request.POST.get("dag_valid") == "1"
#             else SuggestionStatut.REJETER.value
#         )

#         # FIXME: I am not sure we need the filter here
#         suggestion_cohorte_obj.suggestion_unitaires.filter(
#             status=SuggestionStatut.AVALIDER.value
#         ).update(status=new_status)

#         logging.info(f"{suggestion_cohorte_id} - {self.request.user}")

#         suggestion_cohorte_obj.statut = new_status
#         suggestion_cohorte_obj.save()

#         return super().form_valid(form)

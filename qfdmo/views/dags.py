import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic.edit import FormView

from qfdmo.forms import DagsForm
from qfdmo.models.data import DagRun, DagRunStatus


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DagsValidation(IsStaffMixin, FormView):
    form_class = DagsForm
    template_name = "qfdmo/dags_validations.html"
    success_url = "/dags/validations"

    def form_valid(self, form):
        # MANAGE search and display dagrun details
        if self.request.POST.get("search"):
            dagrun = form.cleaned_data["dagrun"]
            context = {"form": form}
            context["dagrun_instance"] = dagrun
            dagrun_lines = dagrun.dagrunchanges.all().order_by("?")[:100]
            context["dagrun_lines"] = dagrun_lines
            return render(self.request, "qfdmo/dags_validations.html", context)

        # ELSE: update the status of the dagrun and its dagrunlines
        dagrun = form.cleaned_data["dagrun"]
        new_status = (
            DagRunStatus.TO_INSERT.value
            if self.request.POST.get("dag_valid") == "1"
            else DagRunStatus.REJECTED.value
        )

        # FIXME: I am not sure we need the filter here
        dagrun.dagrunchanges.filter(status=DagRunStatus.TO_VALIDATE.value).update(
            status=new_status
        )
        dagrun.status = new_status
        dagrun.save()
        messages.success(
            self.request,
            f"La cohorte {dagrun} a été mise à jour avec le statut {new_status}",
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Il y a des erreurs dans le formulaire.")
        return super().form_invalid(form)

    # def form_valid(self, form):
    #     if self.request.POST.get("search"):
    #         messages.add_message(self.request, messages.INFO, "Form Valid.")
    #         return super().form_valid(form)


class DagsValidation1(IsStaffMixin, FormView):
    form_class = DagsForm
    template_name = "qfdmo/dags_validations.html"
    success_url = "/dags/validations"

    def get_initial(self):
        initial = super().get_initial()
        initial["dagrun"] = self.request.GET.get("dagrun")
        return initial

    def post(self, request, *args, **kwargs):

        dag_valid = request.POST.get("dag_valid")
        if dag_valid in ["1", "0"]:
            return self.form_valid(self.get_form())
        else:
            dagrun_obj = DagRun.objects.get(pk=request.POST.get("dagrun"))
            id = request.POST.get("id")
            dagrun_line = dagrun_obj.dagrunchanges.filter(id=id).first()
            identifiant_unique = request.POST.get("identifiant_unique")
            index = request.POST.get("index")
            action = request.POST.get("action")

            if action == "validate":
                dagrun_line.update_row_update_candidate(
                    DagRunStatus.TO_INSERT.value, index
                )
            elif action == "reject":
                dagrun_line.update_row_update_candidate(
                    DagRunStatus.REJECTED.value, index
                )

            updated_candidat = dagrun_line.get_candidat(index)

            return render(
                request,
                "qfdmo/partials/candidat_row.html",
                {
                    "identifiant_unique": identifiant_unique,
                    "candidat": updated_candidat,
                    "index": index,
                    "request": request,
                    "dagrun": request.POST.get("dagrun"),
                    "dagrun_line": dagrun_line,
                },
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("dagrun"):
            dagrun = DagRun.objects.get(pk=self.request.GET.get("dagrun"))
            context["dagrun_instance"] = dagrun
            dagrun_lines = dagrun.dagrunchanges.all().order_by("?")[:100]
            context["dagrun_lines"] = dagrun_lines

            if dagrun_lines and dagrun_lines[0].change_type == "UPDATE_ACTOR":
                # Pagination
                dagrun_lines = dagrun.dagrunchanges.all().order_by("id")
                paginator = Paginator(dagrun_lines, 100)
                page_number = self.request.GET.get("page")
                page_obj = paginator.get_page(page_number)
                context["dagrun_lines"] = page_obj

        return context

    def form_valid(self, form):
        if not form.is_valid():
            raise ValueError("Form is not valid")
        dagrun_id = form.cleaned_data["dagrun"].id
        dagrun_obj = DagRun.objects.get(pk=dagrun_id)
        new_status = (
            DagRunStatus.TO_INSERT.value
            if self.request.POST.get("dag_valid") == "1"
            else DagRunStatus.REJECTED.value
        )

        # FIXME: I am not sure we need the filter here
        dagrun_obj.dagrunchanges.filter(status=DagRunStatus.TO_VALIDATE.value).update(
            status=new_status
        )

        logging.info(f"{dagrun_id} - {self.request.user}")

        dagrun_obj.status = new_status
        dagrun_obj.save()

        return super().form_valid(form)

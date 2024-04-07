import logging

from django.contrib.auth.mixins import LoginRequiredMixin
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

    def get_initial(self):
        initial = super().get_initial()
        initial["dagrun"] = self.request.GET.get("dagrun")
        return initial

    def get_context_data(self, **kwargs):
        if self.request.GET.get("dagrun"):
            dagrun = DagRun.objects.get(pk=self.request.GET.get("dagrun"))
            kwargs["dagrun_instance"] = dagrun
            kwargs["dagrun_lines"] = dagrun.dagrunchanges.all().order_by("?")[:10]
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        dagrun = form.cleaned_data["dagrun"]
        if self.request.POST.get("dag_valid") == "1":
            logging.info(f"Validation of {dagrun} by {self.request.user}")
            dagrun.status = DagRunStatus.TO_INSERT
        else:
            logging.info(f"Rejection of {dagrun} by {self.request.user}")
            dagrun.status = DagRunStatus.REJECTED
        dagrun.save()
        return super().form_valid(form)

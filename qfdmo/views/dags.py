from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from qfdmo.models.data import DagRun, DagRunStatus


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


# TODO : formview with IsStaffMixin
def dags_validations(request):
    dag_runs = DagRun.objects.filter(status=DagRunStatus.TO_VALIDATE)
    return render(
        request,
        "qfdmo/dags_validations.html",
        {
            "dag_runs": dag_runs,
        },
    )

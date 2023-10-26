import logging

from django.contrib.auth.decorators import user_passes_test
from django.db.models import F
from django.shortcuts import render
from django.views.generic.edit import FormView

from qfdmo.forms import GetCorrectionsForm
from qfdmo.models import CorrecteurActeurStatus, CorrectionActeur


class CorrectionsView(FormView):
    form_class = GetCorrectionsForm
    template_name = "qfdmo/corrections.html"

    def get_success_url(self):
        return self.request.path

    def get_initial(self):
        initial = super().get_initial()
        initial["source"] = self.request.GET.get("source", "URL_SCRIPT")
        return initial

    def get_context_data(self, **kwargs):
        kwargs["source"] = self.request.GET.get("source", "URL_SCRIPT")
        kwargs["corrections"] = (
            CorrectionActeur.objects.prefetch_related(
                "final_acteur",
                "final_acteur__proposition_services__sous_categories",
                "final_acteur__proposition_services__sous_categories__categorie",
                "final_acteur__proposition_services__action",
                "final_acteur__proposition_services__action__directions",
                "final_acteur__proposition_services__acteur_service",
                "final_acteur__acteur_type",
            )
            .distinct()
            .filter(
                source=kwargs["source"], correction_statut=CorrecteurActeurStatus.ACTIF
            )
        )
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        logging.warning(request.POST)
        accepted = [key for key, value in request.POST.items() if value == "accept"]
        ignored = [key for key, value in request.POST.items() if value == "ignore"]
        rejected = [key for key, value in request.POST.items() if value == "reject"]
        logging.warning(accepted)
        logging.warning(ignored)
        logging.warning(rejected)
        return super().post(request, *args, **kwargs)


@user_passes_test(lambda user: user.is_staff)
def display_corrections(request):
    # Can be paginate
    corrections_insee = (
        CorrectionActeur.objects.prefetch_related("final_acteur")
        .filter(source="INSEE", correction_statut=CorrecteurActeurStatus.ACTIF)
        .exclude(
            final_acteur__siret=F("siret"),
        )
    )[:1000]
    return render(
        request,
        "qfdmo/corrections.html",
        {
            "corrections": corrections_insee,
        },
    )

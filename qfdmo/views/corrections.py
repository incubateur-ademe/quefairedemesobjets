from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic.edit import FormView

from qfdmo.forms import GetCorrectionsForm
from qfdmo.models import Acteur, ActeurStatus, CorrectionActeur, CorrectionActeurStatus
from qfdmo.thread.materialized_view import RefreshMateriazedViewThread


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


# FIXME : to be tested
class CorrectionsView(IsStaffMixin, FormView):
    form_class = GetCorrectionsForm
    template_name = "qfdmo/corrections.html"

    def get_success_url(self):
        query_params = urlencode(self.request.GET)
        return f"{self.request.path}?{query_params}"

    def get_initial(self):
        initial = super().get_initial()
        initial["source"] = self.request.GET.get("source", "URL_SCRIPT")
        initial["correction_statut"] = self.request.GET.getlist(
            "correction_statut", ["ACTIF"]
        )
        initial["search_query"] = self.request.GET.get("search_query", "")
        initial["nb_lines"] = self.request.GET.get(
            "nb_lines", settings.NB_CORRECTION_DISPLAYED
        )
        return initial

    def get_context_data(self, **kwargs):
        kwargs["source"] = self.request.GET.get("source", "URL_SCRIPT")
        nb_lines = self.request.GET.get("nb_lines", settings.NB_CORRECTION_DISPLAYED)
        correction_statut_list = self.request.GET.getlist(
            "correction_statut", ["ACTIF"]
        )
        corrections = CorrectionActeur.objects.prefetch_related(
            "final_acteur",
            "final_acteur__proposition_services__sous_categories",
            "final_acteur__proposition_services__sous_categories__categorie",
            "final_acteur__proposition_services__action",
            "final_acteur__proposition_services__action__directions",
            "final_acteur__proposition_services__acteur_service",
            "final_acteur__acteur_type",
        ).filter(
            source=kwargs["source"],
            correction_statut__in=correction_statut_list,
            final_acteur__statut=ActeurStatus.ACTIF,
        )
        if search_query := self.request.GET.get("search_query"):
            corrections = corrections.filter(
                Q(final_acteur__nom__icontains=search_query)
                | Q(final_acteur__nom_officiel__icontains=search_query)
                | Q(final_acteur__adresse__icontains=search_query)
                | Q(final_acteur__code_postal__icontains=search_query)
                | Q(final_acteur__ville__icontains=search_query)
            )

        kwargs["nb_corrections"] = corrections.distinct().count()
        kwargs["corrections"] = corrections.distinct()[: int(nb_lines)]
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        accepted = [key for key, value in request.POST.items() if value == "accept"]
        ignored = [key for key, value in request.POST.items() if value == "ignore"]
        rejected = [key for key, value in request.POST.items() if value == "reject"]
        for correction_id in accepted:
            correction = CorrectionActeur.objects.get(id=correction_id)
            acteur = Acteur.objects.get(
                identifiant_unique=correction.identifiant_unique
            )
            revision_acteur = acteur.get_or_create_correctionequipe()
            if correction.source == "URL_SCRIPT":
                revision_acteur.url = correction.url if correction.url else "__nourl__"
                revision_acteur.save()
            if correction.source == "INSEE":
                if (
                    correction.siret is None
                    and correction.naf_principal is None
                    and correction.nom_officiel is None
                ):
                    revision_acteur.statut = ActeurStatus.INACTIF
                else:
                    revision_acteur.siret = correction.siret
                    revision_acteur.naf_principal = correction.naf_principal
                    revision_acteur.nom_officiel = correction.nom_officiel
                revision_acteur.save()
            if correction.source == "RechercheSiret":
                revision_acteur.statut = ActeurStatus.INACTIF
                revision_acteur.save()

            correction.correction_statut = CorrectionActeurStatus.ACCEPTE
            correction.save()
        CorrectionActeur.objects.filter(id__in=ignored).update(
            correction_statut=CorrectionActeurStatus.IGNORE
        )
        CorrectionActeur.objects.filter(id__in=rejected).update(
            correction_statut=CorrectionActeurStatus.REJETE
        )

        RefreshMateriazedViewThread().start()
        return super().post(request, *args, **kwargs)

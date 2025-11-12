from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from data.forms import SuggestionGroupeForm
from data.models.suggestion import SuggestionGroupe, SuggestionUnitaire


class SuggestionGroupeView(LoginRequiredMixin, FormView):
    form_class = SuggestionGroupeForm
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
        print("success url")
        return reverse_lazy(
            "data:suggestion_groupe",
            kwargs={"suggestion_groupe_id": self.kwargs["suggestion_groupe_id"]},
        )

    def get_context_data(self, **kwargs):
        print("context data")
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

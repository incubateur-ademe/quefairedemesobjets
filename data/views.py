from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from data.models.suggestion import SuggestionGroupe


@staff_member_required
def refresh_suggestion_groupe(request, suggestion_groupe_id):
    """
    Vue pour rafraîchir un turbo-frame contenant un groupe de suggestions.
    Utilisée pour mettre à jour l'affichage dynamiquement.
    """
    suggestion_groupe = get_object_or_404(
        SuggestionGroupe.objects.prefetch_related(
            "suggestion_unitaires",
            "acteur",
            "revision_acteur",
            "revision_acteur__parent",
        ),
        id=suggestion_groupe_id,
    )

    return render(
        request,
        "data/_partials/suggestion_groupe_row_type_source.html",
        {
            "suggestion_groupe": suggestion_groupe,
            "suggestion_unitaires_by_champs": (
                suggestion_groupe.get_suggestion_unitaires_by_champs()
            ),
        },
    )

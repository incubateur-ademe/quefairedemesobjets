from django.db.models import Count
from django.shortcuts import render

from qfdmo.models import ActeurReemploi


# Create your views here.
def homepage(request):
    return render(
        request,
        "qfdmo/homepage.html",
    )


def analyse(request):
    acteur_reemplois = (
        ActeurReemploi.objects.all()
        .annotate(acteur_reemploi_revision_count=Count("acteur_reemploi_revisions"))
        .filter(acteur_reemploi_revision_count__gt=1)
        .order_by("-acteur_reemploi_revision_count")
    )

    return render(
        request,
        "qfdmo/analyse.html",
        {
            "acteur_reemplois": acteur_reemplois,
        },
    )


def analyse_acteur_reemploi(request, id):
    acteur_reemploi = ActeurReemploi.objects.get(id=id)
    acteur_reemploi_revisions = (
        acteur_reemploi.acteur_reemploi_revisions.prefetch_related(
            "actions",
            "sous_categories__categorie",
            "entite_type",
        ).all()
    )

    return render(
        request,
        "qfdmo/analyse_acteur_reemploi.html",
        {
            "acteur_reemploi": acteur_reemploi,
            "acteur_reemploi_revisions": acteur_reemploi_revisions,
        },
    )

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ReemploiSolutionView.as_view(), name="reemploi_solution"),
    path("analyse", views.analyse, name="analyse"),
    path(
        "analyse/<int:id>",
        views.analyse_lvao_base,
        name="analyse_lvao_base",
    ),
]

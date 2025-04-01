from django.contrib import admin

from qfdmo.models import CarteConfig, GroupeActionConfig


class GroupeActionConfigInline(admin.StackedInline):
    fields = ("groupe_action", "acteur_type", "icon", "couleur")
    autocomplete_fields = ["groupe_action", "acteur_type"]
    model = GroupeActionConfig
    extra = 0
    verbose_name = "Configuration des groupes d'action associés"


@admin.register(CarteConfig)
class CarteConfigAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["nom"]}
    autocomplete_fields = ["sous_categorie_objet", "source", "groupe_action"]
    inlines = [GroupeActionConfigInline]

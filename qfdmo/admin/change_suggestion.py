from django.contrib.gis import admin

from qfdmo.models.change_suggestion import ChangeSuggestion


class ChangeSuggestionAdmin(admin.ModelAdmin):
    # Pour l'instant on consèrve le modèle admin par défaut
    pass


admin.site.register(ChangeSuggestion, ChangeSuggestionAdmin)

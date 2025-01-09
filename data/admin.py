from django.contrib.gis import admin

from data.models import SuggestionCohorte, SuggestionUnitaire


class SuggestionCohorteAdmin(admin.ModelAdmin):
    pass


class SuggestionUnitaireAdmin(admin.ModelAdmin):
    pass


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(SuggestionUnitaire, SuggestionUnitaireAdmin)

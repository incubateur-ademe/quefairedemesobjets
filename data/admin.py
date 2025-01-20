from django.contrib.gis import admin

from data.models import Suggestion, SuggestionCohorte


class SuggestionCohorteAdmin(admin.ModelAdmin):
    pass


class SuggestionAdmin(admin.ModelAdmin):
    pass


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)

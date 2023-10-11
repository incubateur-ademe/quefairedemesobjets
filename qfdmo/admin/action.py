from django.contrib.gis import admin

from qfdmo.models import Action, ActionDirection


class ActionAdmin(admin.ModelAdmin):
    def get_directions(self, obj):
        return ", ".join([d.nom for d in obj.directions.all()])

    list_display = ("nom", "nom_affiche", "order", "get_directions")
    search_fields = ["nom", "nom_affiche"]


admin.site.register(Action, ActionAdmin)
admin.site.register(ActionDirection)

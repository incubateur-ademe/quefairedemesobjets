from django.contrib.gis import admin

from qfdmo.models import Action, ActionDirection


class ActionAdmin(admin.ModelAdmin):
    def get_directions(self, obj):
        return ", ".join([d.code for d in obj.directions.all()])

    list_display = ("nom", "libelle", "order", "get_directions")
    search_fields = ["nom", "libelle"]


class ActionDirectionAdmin(admin.ModelAdmin):

    list_display = ("nom", "libelle", "order")
    search_fields = ["nom", "libelle"]


admin.site.register(Action, ActionAdmin)
admin.site.register(ActionDirection, ActionDirectionAdmin)

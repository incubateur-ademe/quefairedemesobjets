from django.contrib.gis import admin

from qfdmo.models import Action, ActionDirection, ActionGroup


class ActionAdmin(admin.ModelAdmin):
    def get_directions(self, obj):
        return ", ".join([d.code for d in obj.directions.all()])

    list_display = ("code", "libelle", "order", "get_directions")
    search_fields = ["code", "libelle"]


class ActionDirectionAdmin(admin.ModelAdmin):

    list_display = ("code", "libelle", "order")
    search_fields = ["code", "libelle"]


class ActionGroupAdmin(admin.ModelAdmin):
    list_display = ("code", "libelle", "order")
    search_fields = ["code", "libelle"]


admin.site.register(Action, ActionAdmin)
admin.site.register(ActionGroup, ActionGroupAdmin)
admin.site.register(ActionDirection, ActionDirectionAdmin)

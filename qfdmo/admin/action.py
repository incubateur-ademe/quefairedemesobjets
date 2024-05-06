from django.contrib.gis import admin

from qfdmo.models import Action, ActionDirection, GroupeAction


class ActionAdmin(admin.ModelAdmin):
    def get_directions(self, obj):
        return ", ".join([d.code for d in obj.directions.all()])

    list_display = ("code", "libelle", "order", "get_directions")
    search_fields = ["code", "libelle"]


class ActionDirectionAdmin(admin.ModelAdmin):

    list_display = ("code", "libelle", "order")
    search_fields = ["code", "libelle"]


class GroupeActionAdmin(admin.ModelAdmin):
    list_display = ("code", "libelle", "order")
    search_fields = ["code", "libelle"]


admin.site.register(Action, ActionAdmin)
admin.site.register(GroupeAction, GroupeActionAdmin)
admin.site.register(ActionDirection, ActionDirectionAdmin)

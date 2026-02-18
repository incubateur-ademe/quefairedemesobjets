from django.contrib.gis import admin

from core.admin import CodeLibelleModelMixin, OnlyEditableMixin
from qfdmo.models import Action, ActionDirection, GroupeAction


class ActionAdmin(OnlyEditableMixin, CodeLibelleModelMixin, admin.ModelAdmin):
    list_display = ("code", "libelle", "order", "get_directions")

    def get_directions(self, obj):
        return ", ".join([d.code for d in obj.directions.all()])


class ActionDirectionAdmin(OnlyEditableMixin, CodeLibelleModelMixin, admin.ModelAdmin):
    list_display = ("code", "libelle", "order")


class GroupeActionAdmin(OnlyEditableMixin, CodeLibelleModelMixin, admin.ModelAdmin):
    list_display = ("code", "libelle", "order")
    search_fields = ["code"]


admin.site.register(Action, ActionAdmin)
admin.site.register(GroupeAction, GroupeActionAdmin)
admin.site.register(ActionDirection, ActionDirectionAdmin)

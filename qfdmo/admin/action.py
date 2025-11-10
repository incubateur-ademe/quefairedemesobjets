from django.contrib.gis import admin

from core.admin import CodeLibelleModelMixin, OnlyEditableMixin
from qfdmo.models import Action, Direction, GroupeAction


class ActionAdmin(OnlyEditableMixin, CodeLibelleModelMixin, admin.ModelAdmin):
    list_display = ("code", "libelle", "order", "get_directions")

    def get_directions(self, obj):
        return ", ".join([Direction(code).label for code in obj.direction_codes])


class GroupeActionAdmin(OnlyEditableMixin, CodeLibelleModelMixin, admin.ModelAdmin):
    list_display = ("code", "libelle", "order")
    search_fields = ["code"]


admin.site.register(Action, ActionAdmin)
admin.site.register(GroupeAction, GroupeActionAdmin)

from django.contrib import admin

from qfdmo.models import EPCI


@admin.register(EPCI)
class EPCIAdmin(admin.ModelAdmin):
    search_fields = ["code", "nom"]

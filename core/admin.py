from django.contrib import admin
from django.contrib.postgres.lookups import Unaccent
from django.db.models import CharField, TextField
from django.http import HttpRequest

# Useful to support unaccent lookups in django admin, for
# acteurs and produits for example
CharField.register_lookup(Unaccent)
TextField.register_lookup(Unaccent)


class NotMutableMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class NotEditableMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class OnlyEditableMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class CodeLibelleModelMixin:
    list_display = ("libelle", "code")
    search_fields = ["libelle", "code"]
    search_help_text = "Recherche sur le libellé ou le code"

    # le champ code ne doit pas être modifiable
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["code"]
        return []


class CodeLibelleModelAdmin(CodeLibelleModelMixin, admin.ModelAdmin):
    pass

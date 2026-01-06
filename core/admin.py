from django.conf import settings
from django.contrib import admin
from django.contrib.postgres.lookups import Unaccent
from django.db.models import CharField, TextField
from django.http import HttpRequest

# Useful to support unaccent lookups in django admin, for
# acteurs and produits for example
CharField.register_lookup(Unaccent)
TextField.register_lookup(Unaccent)


class NotMutableMixin:
    # Editable only in debug mode
    # we would like to use permissions but it is not possible as superadmin has all
    # permissions
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return settings.BYPASS_ACTEUR_READONLY_FIELDS

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return settings.BYPASS_ACTEUR_READONLY_FIELDS

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return settings.BYPASS_ACTEUR_READONLY_FIELDS


class NotEditableMixin:
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class NotSelfDeletableMixin(admin.ModelAdmin):
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Allow delete instance only from cascade delete
        """
        return not (
            request.resolver_match
            and request.resolver_match.view_name.startswith(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_"
            )
        )


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

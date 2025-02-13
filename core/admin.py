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

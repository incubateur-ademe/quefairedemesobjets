from django.contrib import admin
from django.contrib.postgres.lookups import Unaccent
from django.core.exceptions import ValidationError
from django.db.models import CharField, Q, TextField
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


class InputFilter(admin.SimpleListFilter):
    """
    A base class for creating custom input-based filters in the Django admin.

    This filter allows free-text input in the admin interface, rather than
    selecting predefined choices. It renders using a custom template
    ("admin/input_filter.html") and supports dynamic query input.

    The `lookups` method returns an empty tuple (required to show the filter),
    and the `choices` method overrides the default behavior to preserve query
    parameters while only showing the "All" choice.

    This class is intended to be subclassed by specific filters that define
    how the queryset should be filtered based on user input.

    Source : https://hakibenita.com/how-to-add-a-text-filter-to-django-admin
    """

    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v)
            for k, values in changelist.get_filters_params().items()
            for v in values
            if k != self.parameter_name
        )
        yield all_choice


class QuerysetFilter(InputFilter):
    """
    A flexible Django admin filter that supports multiple
    dynamic filters and exclusions.

    Format:
        [!]<field>__<lookup>:<value1>[,<value2>][|more_filters...]

    - Use `!` before a query to exclude results.
    - Separate multiple filters with `|`.
    - Multiple values (comma-separated) are OR-ed within a single filter.
    - All filters are AND-ed together (i.e. applied in sequence).

    Examples:
        - 'suggestion__nom__icontains:vivier'
        - '!adresse__istartswith:zac'
        - 'suggestion__nom__icontains:vivier,arbres|!contextes__nom__icontains:zone'

    This enables flexible admin-side searching using Django lookup expressions,
    such as `icontains`, `istartswith`, etc.
    """

    parameter_name = "queryset"
    title = "Queryset"

    def queryset(self, request, queryset):
        raw_input = self.value()

        if not raw_input:
            return

        queryset_parts = [f.strip() for f in raw_input.split("|") if f.strip()]

        for part in queryset_parts:
            is_exclude = part.startswith("!")

            if is_exclude:
                part = part[1:]  # remove the leading !

            try:
                key, values_str = part.split(":", 1)
            except ValueError:
                raise ValidationError(f"Aucun : n'a été détecté dans {part}")

            values = [v.strip() for v in values_str.split(",") if v.strip()]

            if not values:
                continue

            q_obj = Q()

            for val in values:
                q_obj |= Q(**{key: val})

            queryset = queryset.exclude(q_obj) if is_exclude else queryset.filter(q_obj)

        return queryset


class BaseAdmin(admin.ModelAdmin):
    """
    A base Django admin class that automatically adds a custom queryset filter
    to the list of filters in the admin interface.

    This allows all admin classes inheriting from `BaseAdmin` to benefit from
    a dynamic, input-based filtering capability without needing to manually
    declare it in `list_filter`.
    """

    def get_list_filter(self, *args, **kwargs):
        return (QuerysetFilter, *super().get_list_filter(*args, **kwargs))

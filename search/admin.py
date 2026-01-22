from django.contrib import admin

from search.models import SearchTerm


@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    list_display = [
        "term",
        "linked_content_type",
        "linked_object_id",
        "parent_content_type",
        "url",
        "updated_at",
    ]
    list_filter = ["linked_content_type", "parent_content_type"]
    search_fields = ["term", "url"]
    readonly_fields = [
        "linked_content_type",
        "linked_object_id",
        "parent_content_type",
        "parent_object_id",
        "created_at",
        "updated_at",
    ]
    ordering = ["-updated_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("linked_content_type", "parent_content_type")
        )

from django.contrib import admin

from search.models import SearchTerm


@admin.register(SearchTerm)
class SearchTermAdmin(admin.ModelAdmin):
    list_display = ["id", "__str__"]
    search_fields = ["id"]

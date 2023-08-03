from django.contrib import admin

from .models import Category, SubCategory


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "code")
    verbose_name = "Sous-catégorie"
    verbose_name_plural = "Sous-catégories"
    search_fields = [
        "category__name",
        "name",
        "code",
    ]


admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Category)

from django.contrib import admin

from qfdmo.models import Action, Activity, Category, EntityType, SubCategory


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "code")
    search_fields = [
        "category__name",
        "code",
        "name",
    ]


admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Category)
admin.site.register(Action)
admin.site.register(Activity)
admin.site.register(EntityType)

from django.contrib.gis import admin
from django.http.request import HttpRequest

from qfdmo.models import (
    Acteur,
    ActeurService,
    ActeurType,
    Action,
    ActionDirection,
    CategorieObjet,
    FinalActeur,
    FinalPropositionService,
    LVAOBase,
    LVAOBaseRevision,
    PropositionService,
    RevisionActeur,
    RevisionPropositionService,
    SousCategorieObjet,
)
from qfdmo.widget import CustomOSMWidget


class SousCategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "categorie", "code")
    search_fields = [
        "categorie__nom",
        "code",
        "nom",
    ]


class LVAOBaseRevisionAdmin(admin.ModelAdmin):
    list_display = ("nom", "url", "lvao_revision_id")
    ordering = ("lvao_revision_id",)
    search_fields = (
        "nom",
        "url",
        "lvao_revision_id",
        "nom_commercial",
        "nom_officiel",
        "siret",
        "identifiant_externe",
    )
    readonly_fields = ("lvao_base",)


class LVAOBaseRevisionInline(admin.StackedInline):
    model = LVAOBaseRevision
    extra = 0


class LVAOBaseAdmin(admin.ModelAdmin):
    list_display = ("nom", "identifiant_unique")
    search_fields = [
        "nom",
        "identifiant_unique",
    ]
    inlines = [
        LVAOBaseRevisionInline,
    ]


class BasePropositionServiceInline(admin.TabularInline):
    extra = 0

    fields = (
        "action",
        "acteur_service",
        "sous_categories",
    )

    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)


class PropositionServiceInline(BasePropositionServiceInline):
    model = PropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class RevisionPropositionServiceInline(BasePropositionServiceInline):
    model = RevisionPropositionService


class FinalPropositionServiceInline(BasePropositionServiceInline):
    model = FinalPropositionService

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class NotEditableMixin(admin.GISModelAdmin):
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


class BaseActeurAdmin(admin.GISModelAdmin):
    gis_widget = CustomOSMWidget
    inlines = [
        PropositionServiceInline,
    ]
    list_display = ("nom", "siret", "identifiant_unique", "code_postal", "ville")
    search_fields = [
        "code_postal",
        "identifiant_unique",
        "nom",
        "siret",
        "ville",
    ]


class ActeurAdmin(BaseActeurAdmin, NotEditableMixin):
    change_form_template = "admin/acteur/change_form.html"

    ordering = ("nom",)


class RevisionActeurAdmin(BaseActeurAdmin):
    gis_widget = CustomOSMWidget
    inlines = [
        RevisionPropositionServiceInline,
    ]
    exclude = ["id"]


class FinalActeurAdmin(BaseActeurAdmin, NotEditableMixin):
    gis_widget = CustomOSMWidget
    inlines = [
        FinalPropositionServiceInline,
    ]


class ActionAdmin(admin.ModelAdmin):
    def get_directions(self, obj):
        return ", ".join([d.nom for d in obj.directions.all()])

    list_display = ("nom", "nom_affiche", "order", "get_directions")
    search_fields = ["nom", "nom_affiche"]


admin.site.register(SousCategorieObjet, SousCategorieAdmin)
admin.site.register(CategorieObjet)
admin.site.register(Action, ActionAdmin)
admin.site.register(ActionDirection)
admin.site.register(ActeurService)
admin.site.register(ActeurType)
admin.site.register(LVAOBase, LVAOBaseAdmin)
admin.site.register(LVAOBaseRevision, LVAOBaseRevisionAdmin)
admin.site.register(Acteur, ActeurAdmin)
admin.site.register(RevisionActeur, RevisionActeurAdmin)
admin.site.register(FinalActeur, FinalActeurAdmin)

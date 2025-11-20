from django.contrib import admin

from qfdmo.models import CarteConfig, GroupeActionConfig


class GroupeActionConfigInline(admin.StackedInline):
    fields = ("groupe_action", "acteur_type", "icon")
    autocomplete_fields = ["groupe_action", "acteur_type"]
    model = GroupeActionConfig
    extra = 0
    verbose_name = "Configuration des groupes d'action associés"


@admin.register(CarteConfig)
class CarteConfigAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["nom"]}
    autocomplete_fields = [
        "sous_categorie_objet",
        "source",
        "groupe_action",
        "action",
        "direction",
        "epci",
        "acteur_type",
        "label_qualite",
    ]
    fieldsets = (
        (
            "Informations générales",
            {
                "fields": (
                    "nom",
                    "slug",
                )
            },
        ),
        (
            "Actions et directions",
            {
                "fields": (
                    "groupe_action",
                    "action",
                    "direction",
                ),
                "description": "Définir les actions et directions visibles sur"
                " la carte",
            },
        ),
        (
            "Filtres de données",
            {
                "fields": (
                    "sous_categorie_objet",
                    "acteur_type",
                    "source",
                    "label_qualite",
                    "epci",
                ),
                "description": "Filtrer les acteurs et objets affichés sur la carte",
            },
        ),
        (
            "Options d'affichage",
            {
                "fields": (
                    "mode_affichage",
                    "nombre_d_acteurs_affiches",
                    "cacher_legende",
                    "supprimer_branding",
                )
            },
        ),
        (
            "Écran de prévisualisation",
            {
                "fields": (
                    "titre_previsualisation",
                    "contenu_previsualisation",
                ),
                "description": "Contenu affiché avant qu'une recherche ne soit"
                " effectuée",
                "classes": ("collapse",),
            },
        ),
        (
            "Paramètres avancés (temporaire)",
            {
                "fields": (
                    "SOLUTION_TEMPORAIRE_A_SUPPRIMER_DES_QUE_POSSIBLE_parametres_url",
                ),
                "classes": ("collapse",),
                "description": "⚠️ Champ temporaire à supprimer dès que possible",
            },
        ),
    )
    inlines = [GroupeActionConfigInline]

import json
import logging
import re
from typing import Any

from decouple import config
from django.contrib import admin, messages
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html
from djangoql.admin import DjangoQLSearchMixin

from core.admin import NotEditableMixin, NotSelfDeletableMixin, QuerysetFilterAdmin
from data.models.suggestion import (
    Suggestion,
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionLog,
    SuggestionStatut,
    SuggestionUnitaire,
)

NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING = 100

logger = logging.getLogger(__name__)


class LLMQueryBuilder:
    """
    Sandbox for LLM-powered queryset building.
    This class ensures read-only operations and safe query generation.
    """

    def __init__(self, model_class):
        self.model_class = model_class
        # Try both ANTHROPIC_API_KEY and ANTHROPIC_KEY for compatibility
        self.api_key = config(
            "ANTHROPIC_API_KEY", default=config("ANTHROPIC_KEY", default="")
        )

    def _get_model_schema(self) -> str:
        """Generate a schema description for the model."""
        fields = []
        for field in self.model_class._meta.get_fields():
            if hasattr(field, "get_internal_type"):
                field_type = field.get_internal_type()
                field_info = f"- {field.name}: {field_type}"

                # Add choices if available
                if hasattr(field, "choices") and field.choices:
                    field_info += f" (choices: {field.choices})"

                # Add special note for JSONField
                if field_type == "JSONField" and field.name == "metadata":
                    field_info += (
                        "\n  * For metadata field, use Django JSON lookups like:\n"
                        "    - metadata__1) 📦 Nombre Clusters Proposés__gte for cluster count\n"
                        "    - metadata__has_key to check if key exists\n"
                        "  * Common metadata keys for CLUSTERING type:\n"
                        '    - "1) 📦 Nombre Clusters Proposés" (cluster count)\n'
                        '    - "4) 🎭 Nombre Acteurs Total" (total actors)\n'
                    )

                fields.append(field_info)
        return "\n".join(fields)

    def _call_llm(self, search_query: str) -> dict:
        """Call the LLM API to generate filter parameters."""
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not configured, skipping LLM search")
            return {}

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            model_schema = self._get_model_schema()
            model_name = self.model_class.__name__

            prompt = f"""You are a Django ORM query builder assistant. Your task is to convert natural language search queries into Django QuerySet filter parameters.

Model: {model_name}
Available fields:
{model_schema}

User search query: "{search_query}"

Generate a JSON object containing Django filter parameters that can be used with QuerySet.filter(**params).
Only use fields that exist in the model schema above.
Use Django ORM lookup syntax like __icontains, __exact, __gte, __lte, __gt, __lt, etc.

IMPORTANT EXAMPLES:

1) For JSONField queries (metadata field), use the exact key path:
   Query: "cohortes with more than 200 clusters proposed"
   Response: {{"filters": {{"metadata__1) 📦 Nombre Clusters Proposés__gte": 200}}}}

2) For simple text searches:
   Query: "enrichment actions"
   Response: {{"filters": {{"type_action__icontains": "ENRICH"}}}}

3) For status filters:
   Query: "failed suggestions"
   Response: {{"filters": {{"statut__exact": "ERREUR"}}}}

4) For Q objects with OR/AND logic:
   Query: "pending or in progress"
   Response: {{
       "q_objects": [
           {{"statut__exact": "AVALIDER", "connector": "OR"}},
           {{"statut__exact": "ENCOURS", "connector": "OR"}}
       ]
   }}

5) Combining filters:
   Query: "clustering cohortes with more than 100 clusters"
   Response: {{
       "filters": {{
           "type_action__exact": "CLUSTERING",
           "metadata__1) 📦 Nombre Clusters Proposés__gte": 100
       }}
   }}

For simple filters, return:
{{
    "filters": {{
        "field__lookup": "value",
        "another_field__icontains": "text"
    }}
}}

For Q objects with OR/AND logic, return:
{{
    "q_objects": [
        {{"field__lookup": "value", "connector": "OR"}},
        {{"field__lookup": "value", "connector": "AND"}}
    ]
}}

IMPORTANT:
- Only generate READ operations. Never suggest create, update, or delete operations.
- For JSONField metadata queries, use the EXACT key name from the schema (including emojis and special characters)
- When the user mentions "clusters", "clusters proposés", or "nombre de clusters", use the key "1) 📦 Nombre Clusters Proposés"
- Return ONLY the JSON object, no explanation or markdown formatting."""

            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            return {}

    def build_queryset(self, queryset: QuerySet, search_query: str) -> QuerySet:
        """
        Build a filtered queryset based on natural language search.
        This method is sandboxed to only perform read operations.
        """
        if not search_query or not self.api_key:
            logger.info(
                f"LLM search skipped: search_query={bool(search_query)}, "
                f"api_key_configured={bool(self.api_key)}"
            )
            return queryset

        logger.info(f"LLM search query: '{search_query}'")
        llm_response = self._call_llm(search_query)

        if not llm_response:
            logger.warning(f"LLM returned empty response for query: '{search_query}'")
            return queryset

        logger.info(f"LLM response: {json.dumps(llm_response, indent=2)}")

        try:
            # Handle Q objects for complex queries
            if "q_objects" in llm_response:
                q_filter = Q()
                for q_obj in llm_response["q_objects"]:
                    connector = q_obj.pop("connector", "AND")
                    q_item = Q(**q_obj)
                    if connector == "OR":
                        q_filter |= q_item
                    else:
                        q_filter &= q_item
                queryset = queryset.filter(q_filter)
                logger.info(f"Applied Q objects filter. SQL: {queryset.query}")

            # Handle simple filters
            elif "filters" in llm_response:
                # Validate field names before applying filters
                valid_fields = {
                    field.name for field in self.model_class._meta.get_fields()
                }
                logger.info(f"Valid model fields: {valid_fields}")

                validated_filters = {}
                for key, value in llm_response["filters"].items():
                    # Extract base field name (before first __)
                    # Handle both regular fields and JSON path queries
                    base_field = key.split("__")[0]

                    if base_field in valid_fields:
                        validated_filters[key] = value
                        logger.info(f"✓ Validated filter: {key}={value}")
                    else:
                        logger.warning(
                            f"✗ Ignoring invalid field: {base_field} "
                            f"(not in {valid_fields})"
                        )

                if validated_filters:
                    logger.info(f"Applying validated filters: {validated_filters}")
                    queryset = queryset.filter(**validated_filters)
                    logger.info(
                        f"Applied filters successfully\nGenerated SQL: {queryset.query}"
                    )
                else:
                    logger.warning("No valid filters to apply")

            logger.info(
                f"LLM search completed: {search_query} -> {llm_response}\n"
                f"Final queryset count: {queryset.count()}"
            )

        except Exception as e:
            logger.error(
                f"Error applying LLM-generated filters: {e}\n"
                f"Query: {search_query}\n"
                f"LLM response: {llm_response}",
                exc_info=True,
            )
            # Return original queryset if filtering fails
            return queryset

        return queryset


def dict_to_html_table(data: dict):
    table = "<table class'table-metadata'>"
    for key in sorted(data.keys()):
        if isinstance(data[key], dict):
            value = dict_to_html_table(data[key])
        elif isinstance(data[key], list):
            value = "</td><td>".join([str(item) for item in data[key]])
        else:
            value = data[key]
        table += f"<tr><td>{key}</td><td>{value}</td></tr>"
    table += "</table>"
    return table


class SuggestionLogInline(admin.TabularInline):
    model = SuggestionLog
    fields = (
        "identifiant_unique",
        "niveau_de_log",
        "fonction_de_transformation",
        "origine_colonnes",
        "origine_valeurs",
        "destination_colonnes",
        "message",
    )
    extra = 0
    can_delete = False
    can_add = False
    can_change = False
    can_view = True


class SuggestionCohorteAdmin(DjangoQLSearchMixin, NotEditableMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "__str__",
        "statut",
        "metadonnees",
    ]

    search_fields = ["metadata", "identifiant_action", "identifiant_execution"]
    list_filter = [
        ("statut", admin.ChoicesFieldListFilter),
        ("type_action", admin.ChoicesFieldListFilter),
    ]
    inlines = [SuggestionLogInline]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_query_builder = LLMQueryBuilder(SuggestionCohorte)

    def get_search_results(
        self, request: HttpRequest, queryset: QuerySet, search_term: str
    ) -> tuple[QuerySet, bool]:
        """
        Override search to use LLM-powered natural language queries.
        Falls back to standard search if LLM is not available.
        """
        # Check if search term looks like a natural language query
        # (contains spaces and is not a DjangoQL query)
        is_natural_language = (
            search_term
            and " " in search_term
            and not any(op in search_term for op in ["=", "~", ">", "<", "(", ")", ","])
        )

        if is_natural_language:
            try:
                # Use LLM to build the queryset
                llm_queryset = self.llm_query_builder.build_queryset(
                    queryset, search_term
                )
                # If LLM modified the queryset, use it
                if llm_queryset.query.where:
                    messages.info(
                        request,
                        f"Recherche LLM appliquée pour: '{search_term}'",
                    )
                    return llm_queryset, False
            except Exception as e:
                logger.error(f"LLM search failed, falling back to standard search: {e}")

        # Fall back to default search behavior
        return super().get_search_results(request, queryset, search_term)

    def metadonnees(self, obj):
        return format_html(dict_to_html_table(obj.metadata or {}))

    def get_deleted_objects(self, objs, request):
        """
        Override the Objetcs to delete while removing a SuggestionCohorte because
        in some cases, the list is huge and it is not possible to display it.
        """
        (deletable_objects, model_count, perms_needed, protected) = (
            super().get_deleted_objects(objs, request)
        )
        display_warning = False
        display_deletable_objects = []
        for obj in deletable_objects:
            if (
                isinstance(obj, list | tuple)
                and len(obj) > NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING
            ):
                obj = obj[:NB_SUGGESTIONS_DISPLAYED_WHEN_DELETING]
                display_warning = True
            display_deletable_objects.append(obj)
        if display_warning:
            messages.warning(
                request,
                "Attention : la suppression de cette cohorte entraînera également "
                "la suppression de nombreuses suggestions associées. "
                "Celle-ci ne sont pas toutes listées ici.",
            )

        return display_deletable_objects, model_count, perms_needed, protected


def _manage_suggestion_cohorte_statut(cohorte_ids: list[int]):
    for suggestion_cohorte in SuggestionCohorte.objects.filter(id__in=cohorte_ids):
        # On vérifie si toutes les suggestions de la cohorte sont rejetées
        if Suggestion.objects.filter(
            suggestion_cohorte=suggestion_cohorte,
            statut=SuggestionStatut.AVALIDER,
        ).exists():
            suggestion_cohorte.statut = SuggestionStatut.ENCOURS
        else:
            suggestion_cohorte.statut = SuggestionStatut.SUCCES
        suggestion_cohorte.save()


@admin.action(description="REJETER les suggestions selectionnées")
def mark_as_rejected(self, request, queryset):
    distinct_suggestion_cohorte_ids = queryset.values_list(
        "suggestion_cohorte_id", flat=True
    )
    distinct_suggestion_cohorte_ids = list(set(distinct_suggestion_cohorte_ids))
    queryset.update(statut=SuggestionStatut.REJETEE)
    _manage_suggestion_cohorte_statut(distinct_suggestion_cohorte_ids)
    self.message_user(
        request, f"Les {queryset.count()} suggestions sélectionnées ont été refusées"
    )


@admin.action(description="VALIDER les suggestions selectionnées")
def mark_as_toproceed(self, request, queryset):
    distinct_suggestion_cohorte_ids = queryset.values_list(
        "suggestion_cohorte_id", flat=True
    )
    distinct_suggestion_cohorte_ids = list(set(distinct_suggestion_cohorte_ids))
    queryset.update(statut=SuggestionStatut.ATRAITER)
    _manage_suggestion_cohorte_statut(distinct_suggestion_cohorte_ids)
    self.message_user(
        request,
        f"Les {queryset.count()} suggestions sélectionnées ont été mises à jour"
        " avec le statut «À traiter»",
    )


class SuggestionAdmin(NotSelfDeletableMixin, QuerysetFilterAdmin):
    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    search_fields = ["contexte", "suggestion", "metadata"]
    list_display = [
        "id",
        "cohorte",
        "enrich_statut",
        "donnees_initiales",
        "changements_suggeres",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
    ]
    actions = [mark_as_rejected, mark_as_toproceed]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("suggestion_cohorte")

    def cohorte(self, obj):
        coh = obj.suggestion_cohorte
        return format_html(str(coh).replace(" -- ", "<br/>"))

    def acteur_link_html(self, id):
        return format_html(
            '<a target="_blank" href="/admin/qfdmo/displayedacteur/{}/change/">{}</a>',
            id,
            id,
        )

    def changements_suggeres(self, obj):
        return obj.display_suggestion_details

    def donnees_initiales(self, obj):
        return obj.display_contexte_details

    def enrich_statut(self, obj):
        if (
            obj.statut == SuggestionStatut.ERREUR
            and obj.metadata
            and "error" in obj.metadata
        ):
            return format_html(
                '<span style="color: red;">{}</span><br>{}',
                obj.get_statut_display(),
                obj.metadata["error"],
            )
        return obj.get_statut_display()


class SuggestionUnitaireInline(admin.TabularInline):
    model = SuggestionUnitaire
    # fields = ("statut", "acteur", "revision_acteur", "contexte", "metadata")
    extra = 0
    can_delete = False
    can_add = False
    can_change = False
    can_view = True


@admin.register(SuggestionGroupe)
class SuggestionGroupeAdmin(
    DjangoQLSearchMixin, NotEditableMixin, NotSelfDeletableMixin, QuerysetFilterAdmin
):
    djangoql_completion_enabled_by_default = False

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    search_fields = ["contexte", "metadata"]
    list_display = [
        "id",
        "suggestion_cohorte",
        "statut",
        "acteur",
        "revision_acteur",
        "contexte",
        "metadata",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    inlines = [SuggestionUnitaireInline]
    list_filter = [
        ("suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
    ]
    # actions = [mark_as_rejected, mark_as_toproceed]


@admin.register(SuggestionUnitaire)
class SuggestionUnitaireAdmin(
    DjangoQLSearchMixin,
    NotEditableMixin,
    NotSelfDeletableMixin,
    QuerysetFilterAdmin,
):
    djangoql_completion_enabled_by_default = False

    class SuggestionCohorteFilter(admin.RelatedFieldListFilter):
        def field_choices(self, field, request, model_admin):
            return field.get_choices(include_blank=False, ordering=("-cree_le",))

    list_display = [
        "suggestion_groupe",
        "suggestion_groupe__suggestion_cohorte",
        "statut",
        "acteur",
        "revision_acteur",
        "ordre",
        "raison",
        "parametres",
        "suggestion_modele",
        "champs",
        "valeurs",
    ]

    search_fields = [
        "raison",
        "parametres",
        "suggestion_modele",
        "champs",
        "valeurs",
        "metadata",
    ]
    readonly_fields = ["cree_le", "modifie_le"]
    list_filter = [
        ("suggestion_groupe__suggestion_cohorte", SuggestionCohorteFilter),
        ("statut", admin.ChoicesFieldListFilter),
    ]


admin.site.register(SuggestionCohorte, SuggestionCohorteAdmin)
admin.site.register(Suggestion, SuggestionAdmin)

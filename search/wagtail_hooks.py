import django_filters
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from qfdmd.models import SearchTag, Synonyme, TaggedSearchTag
from search.constants import SEARCH_TAG_HELP_TEXT
from search.models import SearchTerm


class SearchTermViewSet(SnippetViewSet):
    model = SearchTerm
    icon = "search"
    menu_label = "Termes de recherche"
    menu_name = "search-terms"
    list_display = ["__str__", "search_variants"]
    search_fields = ["search_variants"]
    panels = [
        FieldPanel("search_variants"),
    ]


class OrphanFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "choices",
            [
                ("orphan", "Orphelins uniquement"),
                ("linked", "Rattachés uniquement"),
            ],
        )
        kwargs.setdefault("label", "Statut")
        kwargs.setdefault("empty_label", "Tous")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        linked_tag_ids = TaggedSearchTag.objects.values_list("tag_id", flat=True)
        if value == "orphan":
            return qs.exclude(searchterm_ptr_id__in=linked_tag_ids)
        if value == "linked":
            return qs.filter(searchterm_ptr_id__in=linked_tag_ids)
        return qs


class SearchTagFilterSet(WagtailFilterSet):
    status = OrphanFilter()

    class Meta:
        model = SearchTag
        fields = []


class SearchTagViewSet(SnippetViewSet):
    model = SearchTag
    icon = "tag"
    menu_label = "Synonymes de recherche"
    menu_name = "search-tags"
    list_display = ["name"]
    search_fields = ["name"]
    filterset_class = SearchTagFilterSet
    panels = [
        HelpPanel(content=SEARCH_TAG_HELP_TEXT),
        FieldPanel("name"),
        FieldPanel("search_variants"),
    ]


class SynonymeViewSet(SnippetViewSet):
    model = Synonyme
    icon = "doc-full"
    menu_label = "Synonymes (ancienne version)"
    menu_name = "synonymes"
    list_display = ["nom", "modifie_le"]
    search_fields = ["nom"]
    panels = [
        FieldPanel("nom"),
        FieldPanel("disabled"),
        FieldPanel("search_variants"),
    ]


class RechercheViewSetGroup(SnippetViewSetGroup):
    items = (SearchTermViewSet, SearchTagViewSet, SynonymeViewSet)
    menu_icon = "search"
    menu_label = "Moteur de recherche"
    menu_name = "recherche"
    menu_order = 260


register_snippet(RechercheViewSetGroup)

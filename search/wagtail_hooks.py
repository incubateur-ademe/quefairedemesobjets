from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from qfdmd.models import SearchTag, Synonyme
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


class SearchTagViewSet(SnippetViewSet):
    model = SearchTag
    icon = "tag"
    menu_label = "Synonymes de recherche"
    menu_name = "search-tags"
    list_display = ["name"]
    search_fields = ["name"]
    panels = [
        FieldPanel("name"),
        FieldPanel("search_variants"),
    ]


class SynonymeViewSet(SnippetViewSet):
    model = Synonyme
    icon = "doc-full"
    menu_label = "Synonymes (ancienne version)"
    menu_name = "synonymes"
    list_display = ["nom"]
    search_fields = ["nom"]
    panels = [
        FieldPanel("nom"),
        FieldPanel("search_variants"),
    ]


class RechercheViewSetGroup(SnippetViewSetGroup):
    items = (SearchTermViewSet, SearchTagViewSet, SynonymeViewSet)
    menu_icon = "search"
    menu_label = "Recherche"
    menu_name = "recherche"


register_snippet(RechercheViewSetGroup)

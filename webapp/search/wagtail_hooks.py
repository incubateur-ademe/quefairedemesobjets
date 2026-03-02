import django_filters
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.panels import FieldPanel, HelpPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from qfdmd.models import SearchTag, Synonyme, TaggedSearchTag
from search.constants import SEARCH_TAG_HELP_TEXT
from search.models import SearchTerm
from django.conf import settings


class KindFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "choices",
            [
                ("synonyme", "Synonyme (ancienne version)"),
                ("search_tag", "Synonyme de recherche"),
                ("produit_page", "Page produit"),
            ],
        )
        kwargs.setdefault("label", "Type")
        kwargs.setdefault("empty_label", "Tous les types")
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):

        if value == "synonyme":
            return qs.filter(synonyme__isnull=False)
        if value == "search_tag":
            return qs.filter(searchtag__isnull=False)
        if value == "produit_page":
            return qs.filter(produitpagesearchterm__isnull=False)
        return qs


class SearchTermFilterSet(WagtailFilterSet):
    kind = KindFilter()
    disabled = django_filters.BooleanFilter(
        label="Désactivé",
        field_name="disabled",
        widget=django_filters.widgets.BooleanWidget(),
    )

    class Meta:
        model = SearchTerm
        fields = []


class SearchTermViewSet(SnippetViewSet):
    model = SearchTerm
    icon = "search"
    menu_label = "Termes de recherche"
    menu_name = "search-terms"
    list_display = ["__str__", "kind", "redirect_destination", "search_variants"]
    search_backend_name = settings.MODELSEARCH_BACKENDS["default"]["BACKEND"]
    filterset_class = SearchTermFilterSet
    panels = [
        FieldPanel("search_variants"),
        FieldPanel("disabled"),
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
    search_backend_name = settings.MODELSEARCH_BACKENDS["default"]["BACKEND"]
    filterset_class = SearchTagFilterSet
    panels = [
        HelpPanel(content=SEARCH_TAG_HELP_TEXT),
        FieldPanel("name"),
        FieldPanel("disabled"),
        FieldPanel("search_variants"),
    ]


class SynonymeViewSet(SnippetViewSet):
    model = Synonyme
    icon = "doc-full"
    menu_label = "Synonymes (ancienne version)"
    menu_name = "synonymes"
    list_display = ["nom", "modifie_le"]
    search_backend_name = settings.MODELSEARCH_BACKENDS["default"]["BACKEND"]
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

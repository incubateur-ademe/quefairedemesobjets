from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from stats.models import KeyResult
from stats.posthog import InsightSelect


class KeyResultViewSet(SnippetViewSet):
    model = KeyResult
    icon = "table"
    menu_label = "Key results"
    add_to_admin_menu = True
    list_display = ("code", "title", "source", "aggregation", "target")
    panels = [
        FieldPanel("code"),
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("target"),
        MultiFieldPanel(
            [
                FieldPanel("source"),
                FieldPanel("posthog_insight", widget=InsightSelect),
                FieldPanel("aggregation"),
            ],
            heading="Calcul",
        ),
        InlinePanel("values", heading="Valeurs", label="Valeur"),
    ]


register_snippet(KeyResultViewSet)

from django.contrib.gis.db import models
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.admin.panels.publishing_panel import MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet

from qfdmd.blocks import CarteBlock


class Produit(models.Model):
    id = models.IntegerField(
        primary_key=True,
        help_text="Correspond à l'identifiant ID défini dans les données "
        "<i>Que Faire</i>.",
    )
    nom = models.CharField(
        unique=True,
        blank=True,
        help_text="Ce champ est facultatif et n'est utilisé que "
        "dans l'administration Django.",
        verbose_name="Libellé",
    )
    synonymes_existants = models.TextField(blank=True, help_text="Synonymes existants")
    code = models.CharField(blank=True, help_text="Code")
    bdd = models.CharField(blank=True, help_text="Bdd")
    comment_les_eviter = models.TextField(blank=True, help_text="Comment les éviter ?")
    qu_est_ce_que_j_en_fais = models.TextField(
        blank=True, help_text="Qu'est-ce que j'en fais ?"
    )
    que_va_t_il_devenir = models.TextField(
        blank=True, help_text="Que va-t-il devenir ?"
    )
    nom_eco_organisme = models.TextField(blank=True, help_text="Nom de l’éco-organisme")
    filieres_rep = models.TextField(blank=True, help_text="Filière(s) REP concernée(s)")
    slug = models.CharField(blank=True, help_text="Slug - ne pas modifier")
    picto = models.FileField(upload_to="pictos", blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.nom}"

    @cached_property
    def sous_categorie_with_carte_display(self):
        return self.sous_categories.filter(afficher_carte=True).first()

    @cached_property
    def content_display(self) -> list[dict[str, str]]:
        return [
            item
            for item in [
                {
                    "id": "Comment mieux consommer",
                    "title": "Comment mieux consommer",
                    "content": self.comment_les_eviter,
                },
                {
                    "id": "Que va-t-il devenir ?",
                    "title": "Que va-t-il devenir ?",
                    "content": self.que_va_t_il_devenir,
                },
                {
                    "id": "En savoir plus",
                    "title": "En savoir plus",
                    "content": self.que_va_t_il_devenir,
                },
            ]
            if item["content"]
        ]


class Lien(models.Model):
    titre_du_lien = models.CharField(blank=True, unique=True, help_text="Titre du lien")
    url = models.URLField(blank=True, help_text="URL", max_length=300)
    description = models.TextField(blank=True, help_text="Description")
    produits = models.ManyToManyField(
        Produit, related_name="liens", help_text="Produits associés"
    )

    def __str__(self):
        return self.titre_du_lien


class Synonyme(models.Model):
    slug = AutoSlugField(populate_from=["nom"])
    nom = models.CharField(blank=True, unique=True, help_text="Nom du produit")
    produit = models.ForeignKey(
        Produit, related_name="synonymes", on_delete=models.CASCADE
    )

    @property
    def url(self) -> str:
        return self.get_absolute_url()

    def get_absolute_url(self) -> str:
        return reverse("qfdmd:synonyme-detail", args=[self.slug])

    def __str__(self) -> str:
        return self.nom

    class Meta:
        ordering = ("nom",)


class Suggestion(models.Model):
    produit = models.OneToOneField(Synonyme, primary_key=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.produit)


@register_snippet
class ElementReutilisable(models.Model):
    titre = models.CharField(
        help_text="Utilisé uniquement pour retrouver l'élément dans l'administration"
    )
    contenu = RichTextField()
    panels = [FieldPanel("titre"), FieldPanel("contenu")]

    def __str__(self) -> str:
        return self.titre


class ProduitIndexPage(Page):
    max_count = 1


class ProduitPage(Page):
    synonyme = models.OneToOneField(
        "qfdmd.synonyme", on_delete=models.SET_NULL, null=True, blank=True
    )
    infotri = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    content = StreamField(
        [
            ("rich_text", blocks.RichTextBlock()),
            ("heading", blocks.CharBlock()),
        ]
    )

    genre = models.CharField(
        choices=[("m", "Masculin"), ("f", "Féminin"), ("n", "Neutre")]
    )
    nombre = models.CharField(choices=[("s", "Singuler"), ("p", "Pluriel")])
    qqjef_bon_etat = StreamField(
        [
            ("element_reutilisable", SnippetChooserBlock("qfdmd.elementreutilisable")),
            ("rich_text", blocks.RichTextBlock()),
            ("heading", blocks.CharBlock()),
            ("carte", CarteBlock()),
        ],
        verbose_name="Bon état",
    )
    qqjef_mauvais_etat = StreamField(
        [
            ("element_reutilisable", SnippetChooserBlock("qfdmd.elementreutilisable")),
            ("rich_text", blocks.RichTextBlock()),
            ("heading", blocks.CharBlock()),
            ("carte", CarteBlock()),
        ],
        verbose_name="Mauvais état",
    )
    ccr = StreamField(
        [
            ("element_reutilisable", SnippetChooserBlock("qfdmd.elementreutilisable")),
            ("rich_text", blocks.RichTextBlock()),
            ("heading", blocks.CharBlock()),
            ("carte", CarteBlock()),
        ],
        verbose_name="Comment consommer responsable",
    )

    qdti_bon_etat = StreamField(
        [
            ("element_reutilisable", SnippetChooserBlock("qfdmd.elementreutilisable")),
            ("rich_text", blocks.RichTextBlock()),
            ("heading", blocks.CharBlock()),
            ("carte", CarteBlock()),
        ],
        verbose_name="Bon état",
    )
    qdti_mauvais_etat = StreamField(
        [
            ("element_reutilisable", SnippetChooserBlock("qfdmd.elementreutilisable")),
            ("rich_text", blocks.RichTextBlock(label="Texte riche")),
            ("heading", blocks.CharBlock(label="Titre")),
            ("carte", CarteBlock(label="Carte", max_num=1)),
        ],
        verbose_name="Mauvais état",
    )

    content_panels = Page.content_panels + [FieldPanel("content")]

    produit_panels = [
        FieldPanel("infotri"),
        FieldPanel("genre"),
        FieldPanel("nombre"),
        FieldPanel("synonyme"),
    ]

    business_logic_panels = [
        MultiFieldPanel(
            [FieldPanel("qqjef_bon_etat"), FieldPanel("qqjef_mauvais_etat")],
            heading="Qu'est-ce que j'en fait",
            classname="collapsed",
        ),
        FieldPanel("ccr"),
        MultiFieldPanel(
            [FieldPanel("qdti_bon_etat"), FieldPanel("qdti_mauvais_etat")],
            heading="Que devient-il",
            classname="collapsed",
        ),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(
                business_logic_panels, heading="Logique métier", permission="superuser"
            ),
            ObjectList(produit_panels, heading="Produit", permission="superuser"),
            ObjectList(content_panels, heading=_("Contenu")),
            ObjectList(Page.promote_panels, heading=_("Promote")),
            ObjectList(Page.settings_panels, heading=_("Settings")),
        ]
    )

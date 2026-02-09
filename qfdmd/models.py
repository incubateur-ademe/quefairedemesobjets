import logging
from typing import override

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models.functions import Now
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.functional import cached_property
from django_extensions.db.fields import AutoSlugField
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField
from taggit.models import ItemBase, TagBase, TaggedItemBase
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    PageChooserPanel,
    TabbedInterface,
)
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.models import Page, ParentalKey
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from qfdmd.blocks import STREAMFIELD_COMMON_BLOCKS
from qfdmo.models.utils import NomAsNaturalKeyModel
from search.models import SearchTerm

logger = logging.getLogger(__name__)


class GenreNombreModel(models.Model):
    class Genre(models.TextChoices):
        MASCULIN = "m", "Masculin"
        FEMININ = "f", "Féminin"

    class Nombre(models.IntegerChoices):
        SINGULIER = 1, "singulier"
        PLURIEL = 2, "pluriel"

    genre = models.CharField("Genre", blank=True, choices=Genre.choices)
    nombre = models.IntegerField(
        "Nombre", null=True, blank=True, choices=Nombre.choices
    )

    @cached_property
    def pronom(self) -> str:
        if self.nombre == self.Nombre.PLURIEL:
            return "mes"
        if self.genre == self.Genre.FEMININ:
            return "ma"
        return "mon"

    class Meta:
        abstract = True


class CompiledFieldMixin(Page):
    @cached_property
    def famille(self):
        from qfdmd.models import ProduitPage

        """
        Returns the parent ProduitPage if it exists.
        A 'famille' is a ProduitPage that is parent to the current ProduitPage.
        """

        if (
            parent := ProduitPage.objects.filter(est_famille=True)
            .ancestor_of(self)
            .first()
        ):
            return parent

    @cached_property
    def compiled_body(self):
        return self._get_inherited_field("body")

    @cached_property
    def compiled_infotri(self):
        return self._get_inherited_field("infotri")

    @cached_property
    def compiled_titre_phrase(self):
        return self._get_inherited_field("titre_phrase")

    def _get_inherited_field(
        self: Page, field_name: str, disable_inheritance_field=None
    ):
        # TODOWAGTAIL : add unit test
        """
        Retrieve the value of a field from the current page or fall back to its parent.

        This helper is designed for cases where a Produit page
        may not define a certain field and should instead inherit it
        from its parent page.

        An optional "kill switch" field can be used to disable fallback
        and force inheritance even if the field exists on the current page.
        """
        if not hasattr(self, field_name) and getattr(
            self, disable_inheritance_field, True
        ):
            return getattr(self.get_parent().specific, field_name)
        return getattr(self, field_name)

    class Meta:
        abstract = True


class TitleFields(models.Model):
    titre_phrase = models.CharField(
        "Titre utilisé dans les phrases",
        help_text="Ce titre sera utilisé dans les contenus réutilisables, "
        "pour l'affichage du synonyme de recherche",
        blank=True,
    )

    class Meta:
        abstract = True


class ProduitIndexPage(CompiledFieldMixin, Page):
    template = "ui/pages/produit_index_page.html"
    subpage_types = ["qfdmd.produitpage"]
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS,
        verbose_name="Corps de texte",
        blank=True,
    )

    content_panels = Page.content_panels + [FieldPanel("body")]

    @override
    def serve(self, request, *args, **kwargs):
        return redirect(reverse("qfdmd:home"), permanent=False)

    class Meta:
        verbose_name = "Index des familles & produits"


class ProduitPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "qfdmd.ProduitPage",
        on_delete=models.CASCADE,
        related_name="%(class)ss_tagged_items",
    )


class SearchTag(SearchTerm, TagBase):
    """
    A custom tag model for search functionality.
    Inherits from SearchTerm for unified search across different content types.
    """

    search_fields = [
        index.SearchField("name"),
        index.AutocompleteField("name"),
    ]

    class Meta:
        verbose_name = "Synonyme de recherche"
        verbose_name_plural = "Synonymes de recherche"

    @property
    def search_result_template(self):
        return "ui/components/search/_search_result_searchtag.html"

    def get_search_term_verbose_name(self) -> str:
        """Returns the tag name as the search term."""
        return self.name

    @property
    def page(self):
        """Returns the parent page (ProduitPage) if available."""
        try:
            if self.tagged_produit_page:
                return self.tagged_produit_page.content_object
        except TaggedSearchTag.DoesNotExist:
            pass
        return None


class TaggedSearchTag(ItemBase):
    """Through model for SearchTag on ProduitPage."""

    tag = models.OneToOneField(
        SearchTag,
        on_delete=models.CASCADE,
        related_name="tagged_produit_page",
    )
    content_object = ParentalKey(
        "qfdmd.ProduitPage",
        on_delete=models.CASCADE,
        related_name="search_tags_items",
    )

    class Meta:
        verbose_name = "Synonyme de recherche"
        verbose_name_plural = "Synonymes de recherche"


class ProduitPage(
    CompiledFieldMixin,
    Page,
    GenreNombreModel,
    TitleFields,
):
    template = "ui/pages/produit_page.html"
    subpage_types = ["qfdmd.produitpage"]
    parent_page_types = [
        "qfdmd.produitindexpage",
        "qfdmd.produitpage",
    ]

    # Taxonomie
    tags = ClusterTaggableManager(through=ProduitPageTag, blank=True, related_name="+")
    search_tags = ClusterTaggableManager(
        through="qfdmd.TaggedSearchTag",
        blank=True,
        related_name="+",
        verbose_name="Synonyme de recherche",
    )
    sous_categorie_objet = ParentalManyToManyField(
        "qfdmo.SousCategorieObjet",
        related_name="produit_pages",
        blank=True,
    )

    # Config
    usage_unique = models.BooleanField(
        "À usage unique",
        default=False,
    )

    est_famille = models.BooleanField(
        "Est une famille",
        default=False,
        help_text="Si cochée, cette page sera affichée avec le template famille "
        "(fond vert) et pourra contenir des sous-produits.",
    )
    search_variants = models.TextField(
        verbose_name="Variantes de recherche",
        blank=True,
        default="",
        help_text=(
            "Termes alternatifs permettant de trouver cette page dans la recherche. "
            "Ces variantes sont invisibles pour les utilisateurs mais améliorent "
            "la recherche. Séparez les termes par des virgules ou des retours "
            "à la ligne."
        ),
    )

    infotri = StreamField([("image", ImageBlock())], blank=True)
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS,
        verbose_name="Corps de texte",
        blank=True,
    )
    commentaire = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("infotri"),
        FieldPanel("body"),
    ]

    migration_panels = [
        MultiFieldPanel(
            [
                HelpPanel(
                    "<strong>Migration Django → Wagtail</strong><br/>"
                    "Cette page Wagtail remplace une ou plusieurs fiches "
                    "produit Django (ancien système).<br/><br/>"
                    "<strong>Redirection automatique :</strong> Sélectionnez "
                    "les fiches produit Django qui doivent rediriger vers "
                    "cette page Wagtail. Les utilisateurs qui visitent "
                    "l'ancienne URL seront automatiquement redirigés (HTTP 301) "
                    "vers cette nouvelle page."
                ),
                InlinePanel(
                    "legacy_produit",
                    heading="Fiches produit Django à rediriger ici",
                ),
            ],
            heading="Redirection des produits Django",
        ),
        MultiFieldPanel(
            [
                HelpPanel(
                    "<strong>Redirection directe de synonymes</strong><br/>"
                    "Ajoutez ici des synonymes Django qui doivent rediriger "
                    "directement vers cette page Wagtail.<br/><br/>"
                    "<strong>Différence avec les produits :</strong> "
                    "Contrairement aux produits qui redirigent tous leurs "
                    "synonymes, ici vous pouvez sélectionner des synonymes "
                    "individuellement pour les rediriger vers cette page."
                    "<br/><br/>"
                    "<strong>⚠️ Priorité des redirections :</strong> "
                    "Les redirections de synonymes ont la priorité la plus "
                    "élevée. Si un synonyme est listé ici ET que son produit "
                    "est redirigé ailleurs, c'est la redirection du synonyme "
                    "qui sera utilisée. Si vous souhaitez qu'un synonyme ne "
                    "soit pas redirigé du tout, utilisez la section "
                    "'Exceptions aux redirections' ci-dessous."
                ),
                InlinePanel(
                    "legacy_synonymes",
                    heading="Synonymes Django à rediriger ici",
                ),
            ],
            heading="Redirection des synonymes Django",
        ),
        MultiFieldPanel(
            [
                HelpPanel(
                    "<strong>Exceptions aux redirections</strong><br/>"
                    "Par défaut, tous les synonymes d'un produit Django "
                    "sont redirigés avec le produit.<br/><br/>"
                    "<strong>Pour exclure certains synonymes :</strong> "
                    "Si un synonyme doit pointer vers une autre page Wagtail "
                    "(ou ne pas être redirigé), ajoutez-le ici. "
                    "Ces synonymes ne seront pas affectés par la redirection "
                    "configurée ci-dessus."
                ),
                InlinePanel(
                    "legacy_synonymes_to_exclude",
                    heading="Synonymes à ne PAS rediriger",
                ),
            ],
            heading="Exceptions aux redirections",
        ),
        FieldPanel("commentaire"),
    ]

    config_panels = [
        MultiFieldPanel(
            [
                FieldPanel("titre_phrase"),
                FieldRowPanel(
                    [FieldPanel("genre"), FieldPanel("nombre")],
                    heading="Genre et nombre",
                ),
            ],
            heading="Dynamisation des contenus",
        ),
        MultiFieldPanel(
            [
                FieldPanel("est_famille"),
                FieldPanel("usage_unique"),
                FieldPanel("tags"),
                FieldPanel("search_tags"),
                FieldPanel("search_variants"),
                FieldPanel("sous_categorie_objet"),
            ],
            heading="Taxonomie",
        ),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Contenu"),
            ObjectList(config_panels, heading="Configuration"),
            ObjectList(migration_panels, heading="Migration"),
            ObjectList(Page.promote_panels, heading="Promotion (SEO)"),
            ObjectList(Page.settings_panels, heading="Paramètres"),
        ],
    )

    search_fields = Page.search_fields + [
        index.AutocompleteField("title"),
        index.AutocompleteField("search_variants", boost=2.0),
        index.SearchField("search_variants", boost=2.0),
    ]

    def clean(self):
        super().clean()

        # Validate legacy_synonyme inline items
        for synonyme_item in self.legacy_synonymes.all():
            try:
                synonyme = synonyme_item.synonyme
            except Synonyme.DoesNotExist:
                # The related synonyme was deleted, skip validation
                continue

            if synonyme:
                # Check if the synonyme's produit is already redirected
                try:
                    produit_page = synonyme.produit.next_wagtail_page
                    if produit_page.page != self:
                        logger.warning(
                            f"Synonyme '{synonyme.nom}' has a direct "
                            f"redirection to page '{self.title}' but its "
                            f"produit '{synonyme.produit.nom}' is "
                            f"redirected to '{produit_page.page.title}'. "
                            "The synonyme redirection will take priority."
                        )
                except Exception:
                    # If produit has no redirection or any other error, that's fine
                    pass

                # Check if this synonyme is marked as excluded somewhere else
                try:
                    exclusion = (
                        LegacyIntermediateProduitPageSynonymeExclusion.objects.get(
                            synonyme=synonyme
                        )
                    )
                    if exclusion.page != self:
                        raise ValidationError(
                            f"Conflit : le synonyme '{synonyme.nom}' "
                            "est marqué comme exclu de la redirection vers la page "
                            f"'{exclusion.page.title}'. "
                            "Vous ne pouvez pas créer une redirection directe "
                            "tant que cette exclusion existe. "
                            "Veuillez d'abord supprimer l'exclusion."
                        )
                except LegacyIntermediateProduitPageSynonymeExclusion.DoesNotExist:
                    # No exclusion exists, that's fine
                    pass

    @property
    def search_result_template(self):
        return "ui/components/search/_search_result_produitpage.html"

    def get_template(self, request, *args, **kwargs):
        if self.est_famille:
            return "ui/pages/family_page.html"
        return "ui/pages/produit_page.html"

    class Meta:
        verbose_name = "Produit"


# LEGACY MODELS
# ==============
class LegacyIntermediateProduitPage(models.Model):
    page = ParentalKey(
        "wagtailcore.page",
        on_delete=models.CASCADE,
        related_name="legacy_produit",
    )
    produit = models.OneToOneField(
        "qfdmd.produit",
        on_delete=models.CASCADE,
        related_name="next_wagtail_page",
    )

    panels = [FieldPanel("produit")]

    class Meta:
        verbose_name = "Fiche produit"
        verbose_name_plural = "Fiches produit"


class LegacyIntermediateProduitPageSynonymeExclusion(models.Model):
    page = ParentalKey(
        "wagtailcore.page",
        on_delete=models.CASCADE,
        related_name="legacy_synonymes_to_exclude",
    )
    synonyme = models.OneToOneField(
        "qfdmd.synonyme",
        on_delete=models.CASCADE,
        related_name="should_not_redirect_to",
    )

    panels = [FieldPanel("synonyme")]

    def clean(self):
        super().clean()

        if self.synonyme:
            # Check if this synonyme has a direct redirection elsewhere
            try:
                direct_redirection = self.synonyme.next_wagtail_page
                raise ValidationError(
                    f"Conflit : ce synonyme a déjà une redirection directe "
                    f"vers la page '{direct_redirection.page.title}'. "
                    f"Vous ne pouvez pas l'exclure ici. "
                    f"Veuillez d'abord supprimer la redirection directe "
                    f"du synonyme."
                )
            except Synonyme.next_wagtail_page.RelatedObjectDoesNotExist:
                # No direct redirection exists, that's fine
                pass

    class Meta:
        verbose_name = "Fiche synonyme"
        verbose_name_plural = "Fiches synonyme"


class LegacyIntermediateSynonymePage(models.Model):
    page = ParentalKey(
        "wagtailcore.page",
        on_delete=models.CASCADE,
        related_name="legacy_synonymes",
    )
    synonyme = models.OneToOneField(
        "qfdmd.synonyme",
        on_delete=models.CASCADE,
        related_name="next_wagtail_page",
    )

    panels = [FieldPanel("synonyme")]

    class Meta:
        verbose_name = "Fiche synonyme"
        verbose_name_plural = "Fiches synonyme"


class AbstractBaseProduit(NomAsNaturalKeyModel):
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
    # Le nom des champs conserve ici délibérément l'ancienne nomenclature,
    # car le travail sur le nommage n'a pas encore été effectué.
    # TODO : renommer ces champs lorsque le métier + technique seront tombés
    # d'accord sur un nom pour ces champs
    qu_est_ce_que_j_en_fais_mauvais_etat = models.TextField(
        blank=True,
        help_text="Qu'est-ce que j'en fais ? - Mauvais état",
    )
    # TODO : idem ci-dessus
    qu_est_ce_que_j_en_fais_bon_etat = models.TextField(
        blank=True,
        help_text="Qu'est-ce que j'en fais ? - Bon état",
    )
    comment_les_eviter = models.TextField(
        blank=True,
        help_text="Comment consommer responsable ?",
    )
    que_va_t_il_devenir = models.TextField(
        blank=True,
        help_text="Que va-t-il devenir ?",
    )

    class Meta:
        abstract = True
        ordering = ("id",)


@register_snippet
class Produit(index.Indexed, AbstractBaseProduit):
    @cached_property
    def bon_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_bon_etat:
            return self.qu_est_ce_que_j_en_fais_bon_etat
        try:
            return self.get_etats_descriptions()[1]
        except (KeyError, TypeError):
            return ""

    @cached_property
    def mauvais_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_mauvais_etat:
            return self.qu_est_ce_que_j_en_fais_mauvais_etat
        try:
            return self.get_etats_descriptions()[0]
        except (KeyError, TypeError):
            return ""

    id = models.AutoField(
        primary_key=True,
        help_text="A l'origine : Correspond à l'identifiant ID défini dans les données "
        "<i>Que Faire</i>. Maintenant : Identifiant auto-généré.",
    )

    nom = models.CharField(
        unique=True,
        verbose_name="Libellé",
    )
    synonymes_existants = models.TextField(
        blank=True,
        help_text="Ce champ est obsolète,"
        " il n'est actuellement pas mis à jour automatiquement.",
    )
    code = models.CharField(blank=True, help_text="Code")
    bdd = models.CharField(blank=True, help_text="Bdd")
    qu_est_ce_que_j_en_fais = models.TextField(
        blank=True,
        help_text="Qu'est-ce que j'en fais ? - ANCIEN CHAMP.",
    )
    nom_eco_organisme = models.CharField(blank=True, help_text="Nom de l’éco-organisme")
    filieres_rep = models.CharField(blank=True, help_text="Filière(s) REP concernée(s)")
    slug = models.CharField(blank=True, help_text="Slug - ne pas modifier")
    infotri = StreamField([("image", ImageBlock())], blank=True)

    panels = [FieldPanel("infotri")]

    def __str__(self):
        return f"{self.pk} - {self.nom}"

    search_fields = [
        index.AutocompleteField("nom"),
        index.RelatedFields("synonymes", [index.SearchField("nom")]),
        index.SearchField("id"),
    ]

    @cached_property
    def sous_categorie_with_carte_display(self):
        return self.sous_categories.filter(afficher_carte=True).first()

    def get_etats_descriptions(self) -> tuple[str, str] | None:
        # TODO: rename this method
        # Une fois que les fiches déchet auront toutes
        # la notion de bon etat / mauvais état stockée en
        # base de donnée au bon endroit, cette méthode deviendra caduque.
        text = self.qu_est_ce_que_j_en_fais
        if "En bon état" not in text and "En mauvais état" not in text:
            return None

        _, _, mauvais_etat_and_rest = text.partition("<b>En bon état</b>")
        mauvais_etat, _, bon_etat = mauvais_etat_and_rest.partition(
            "<b>En mauvais état</b>",
        )

        return (bon_etat, mauvais_etat)

    @property
    def carte_settings(self):
        # TODO : gérer plusieurs catégories ici
        sous_categorie = self.sous_categories.filter(afficher_carte=True).first()
        if not sous_categorie:
            return {}

        return {
            "direction": "jai",
            "sc_id": sous_categorie.id,
            "sous_categorie_objet": sous_categorie.libelle,
        }

    @cached_property
    def en_savoir_plus(self):
        produit_liens = (
            ProduitLien.objects.filter(produit=self)
            .select_related("lien")
            .order_by("poids")
        )

        if not produit_liens:
            return None

        return render_to_string(
            "ui/components/produit/_en_savoir_plus.html",
            {"liens": [produit_lien.lien for produit_lien in produit_liens]},
        )

    @cached_property
    def content_display(self) -> list[dict[str, str]]:
        return [
            item
            for item in [
                {
                    "id": "Que va-t-il devenir ?",
                    "title": "Que va-t-il devenir ?",
                    "content": self.que_va_t_il_devenir,
                },
                {
                    "id": "Comment consommer responsable ?",
                    "title": "Comment consommer responsable ?",
                    "content": self.comment_les_eviter,
                },
                {
                    "id": "En savoir plus",
                    "title": "En savoir plus",
                    "content": self.en_savoir_plus,
                },
            ]
            if item["content"]
        ]


@register_snippet
class Lien(models.Model):
    titre_du_lien = models.CharField(blank=True, unique=True, help_text="Titre du lien")
    url = models.URLField(blank=True, help_text="URL", max_length=300)
    description = models.TextField(blank=True, help_text="Description")
    produits = models.ManyToManyField(
        Produit,
        through="qfdmd.ProduitLien",
        related_name="liens",
        help_text="Produits associés",
    )

    def __str__(self):
        return self.titre_du_lien

    class Meta:
        ordering = ("titre_du_lien",)


class ProduitLien(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    lien = models.ForeignKey(Lien, on_delete=models.CASCADE)
    poids = models.IntegerField(
        default=0,
        help_text=(
            "Ce champ détermine la position d'un élément dans la liste affichée.<br>"
            "Les éléments avec un poids plus élevé apparaissent plus bas dans "
            "la liste.<br>"
            "Les éléments avec un poids plus faible apparaissent plus haut."
        ),
    )

    class Meta:
        ordering = ("poids",)
        unique_together = ("produit", "lien")  # Prevent duplicate relations


class Synonyme(SearchTerm, AbstractBaseProduit):
    slug = AutoSlugField(populate_from=["nom"], max_length=255)
    nom = models.CharField(blank=True, unique=True, help_text="Nom du produit")
    produit = models.ForeignKey(
        Produit,
        related_name="synonymes",
        on_delete=models.CASCADE,
    )
    imported_as_search_tag = models.ForeignKey(
        "qfdmd.SearchTag",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imported_synonymes",
        verbose_name="Importé comme SearchTag",
        help_text="Si renseigné, ce synonyme a été importé comme SearchTag "
        "et ne devrait plus apparaître dans les résultats de recherche.",
    )
    picto = models.FileField(
        upload_to="pictos",
        blank=True,
        null=True,
        help_text="Ce pictogramme est affiché en page d'accueil "
        "s'il est renseigné et si la case ci-dessous est cochée.",
    )
    pin_on_homepage = models.BooleanField(
        "Épingler en page d'accueil",
        default=False,
        help_text="Si un pictogramme est renseigné pour ce synonyme, "
        "celui-ci s'affichera en page d'accueil. À noter : seuls les "
        "30 premiers synonymes avec la case cochée s'afficheront.",
    )
    meta_description = models.TextField(
        "Description lue et affichée par les moteurs de recherche.",
        blank=True,
    )

    @property
    def url(self) -> str:
        return self.get_absolute_url()

    @cached_property
    def bon_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_bon_etat:
            return self.qu_est_ce_que_j_en_fais_bon_etat
        if self.produit.qu_est_ce_que_j_en_fais_bon_etat:
            return self.produit.qu_est_ce_que_j_en_fais_bon_etat

        try:
            return self.produit.get_etats_descriptions()[1]
        except (KeyError, TypeError):
            return ""

    @cached_property
    def mauvais_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_mauvais_etat:
            return self.qu_est_ce_que_j_en_fais_mauvais_etat
        if self.produit.qu_est_ce_que_j_en_fais_mauvais_etat:
            return self.produit.qu_est_ce_que_j_en_fais_mauvais_etat

        try:
            return self.produit.get_etats_descriptions()[0]
        except (KeyError, TypeError):
            return ""

    def get_absolute_url(self) -> str:
        return reverse("qfdmd:synonyme-detail", args=[self.slug])

    def __str__(self) -> str:
        return self.nom

    search_fields = [
        index.SearchField("nom"),
        index.AutocompleteField("nom"),
    ]

    @property
    def search_result_template(self):
        return "ui/components/search/_search_result_synonyme.html"

    def get_search_term_verbose_name(self) -> str:
        """Returns the synonyme name as the search term."""
        return self.nom

    def get_search_term_url(self) -> str:
        """Returns the URL of the synonyme detail page."""
        return self.get_absolute_url()

    def get_search_term_parent_object(self):
        """Returns None for legacy synonymes."""
        return None


@register_setting
class FormPageValidationSettings(BaseGenericSetting):
    form_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Sélectionnez la page de formulaire utilisée pour "
        " le formulaire de contact. Celle-ci doit avoir exactement 4 champs",
    )

    panels = [
        PageChooserPanel("form_page", "sites_faciles_forms.FormPage"),
    ]

    class Meta:
        verbose_name = "Paramètres des pages de formulaire"


@register_setting
class EmbedSettings(BaseGenericSetting):
    backlink_assistant = RichTextField(
        "Backlink de l'iframe de l'assistant", blank=True
    )
    backlink_carte = RichTextField("Backlink de l'iframe de la carte", blank=True)
    backlink_formulaire = RichTextField(
        "Backlink de l'iframe du formulaire", blank=True
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("backlink_assistant"),
                FieldPanel("backlink_carte"),
                FieldPanel("backlink_formulaire"),
                HelpPanel(
                    "Les backlink sont cachés pendant dix minutes.\n"
                    "Cela veut dire qu'une mise à jour du contenu ci-dessus "
                    "ne sera reflétée qu'après ce délai."
                ),
            ],
            heading="Backlink",
        )
    ]

    class Meta:
        verbose_name = "Réglage des iframes"

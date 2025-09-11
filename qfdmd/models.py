import logging
from urllib.parse import urlencode

from django.contrib.gis.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Now
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django_extensions.db.fields import AutoSlugField
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.models import Page, ParentalKey
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from core.models.mixin import TimestampedModel
from qfdmd.blocks import STREAMFIELD_COMMON_BLOCKS
from qfdmo.models.utils import NomAsNaturalKeyModel

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

    class Meta:
        abstract = True


@register_snippet
class Bonus(index.Indexed, models.Model):
    title = models.CharField(unique=True)
    montant_min = models.IntegerField()
    montant_max = models.IntegerField(null=True)

    search_fields = [
        index.SearchField("title"),
        index.AutocompleteField("title"),
    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Bonus"
        verbose_name = "Bonus"


@register_snippet
class ReusableContent(index.Indexed, models.Model):
    title = models.CharField(verbose_name="Titre", unique=True)
    feminin_singulier = RichTextField(verbose_name="Contenu - Féminin singulier")
    feminin_pluriel = RichTextField(verbose_name="Contenu - Féminin pluriel")
    masculin_singulier = RichTextField(verbose_name="Contenu - Masculin singulier")
    masculin_pluriel = RichTextField(verbose_name="Contenu - Masculin pluriel")

    search_fields = [
        index.SearchField("title"),
        index.AutocompleteField("title"),
    ]

    panels = [
        FieldPanel("title"),
        FieldPanel("feminin_singulier"),
        FieldPanel("feminin_pluriel"),
        FieldPanel("masculin_singulier"),
        FieldPanel("masculin_pluriel"),
    ]

    def get_from_genre_nombre(
        self,
        genre: str,
        nombre: int,
    ):
        if (
            genre == GenreNombreModel.Genre.MASCULIN
            and nombre == GenreNombreModel.Nombre.SINGULIER
        ):
            return self.masculin_singulier

        if (
            genre == GenreNombreModel.Genre.FEMININ
            and nombre == GenreNombreModel.Nombre.SINGULIER
        ):
            return self.feminin_singulier
        if (
            genre == GenreNombreModel.Genre.MASCULIN
            and nombre == GenreNombreModel.Nombre.PLURIEL
        ):
            return self.masculin_pluriel

        if (
            genre == GenreNombreModel.Genre.FEMININ
            and nombre == GenreNombreModel.Nombre.PLURIEL
        ):
            return self.feminin_pluriel

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Contenu réutilisable"
        verbose_name_plural = "Contenus réutilisables"


class CompiledFieldMixin(Page):
    @cached_property
    def famille(self):
        if famille := self.get_ancestors().type(FamilyPage).first():
            return famille

    @cached_property
    def compiled_body(self):
        return self._get_inherited_field("body")

    @cached_property
    def compiled_bonus(self):
        return self._get_inherited_field("bonus", "disable_bonus_inheritance")

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
    subpage_types = ["qfdmd.produitpage", "qfdmd.familypage"]

    class Meta:
        verbose_name = "Index des familles & produits"


class ProduitPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "qfdmd.ProduitPage",
        on_delete=models.CASCADE,
        related_name="%(class)ss_tagged_items",
    )


class AncestorFieldsMixin:
    @property
    def family(self):
        return FamilyPage.objects.ancestor_of(self).first()


class ProduitPage(
    CompiledFieldMixin, Page, GenreNombreModel, TitleFields, AncestorFieldsMixin
):
    subpage_types = [
        "qfdmd.synonymepage",
    ]
    parent_page_types = ["qfdmd.produitindexpage", "qfdmd.familypage"]

    # Taxonomie
    tags = ClusterTaggableManager(through=ProduitPageTag, blank=True, related_name="+")
    sous_categorie_objet = ParentalManyToManyField(
        "qfdmo.SousCategorieObjet",
        related_name="produit_pages",
        blank=True,
    )

    # Config
    bonus = models.ForeignKey(
        "qfdmd.bonus",
        on_delete=models.SET_NULL,
        related_name="produit_page",
        blank=True,
        null=True,
    )
    disable_bonus_inheritance = models.BooleanField(
        "Désactiver l'héritage du bonus",
        default=False,
    )
    legacy_produit = models.ForeignKey(
        "qfdmd.produit",
        on_delete=models.SET_NULL,
        related_name="produit_page",
        blank=True,
        null=True,
    )
    legacy_synonyme = models.ForeignKey(
        "qfdmd.synonyme",
        on_delete=models.SET_NULL,
        related_name="produit_page",
        blank=True,
        null=True,
    )

    usage_unique = models.BooleanField(
        "À usage unique",
        default=False,
    )

    infotri = StreamField([("image", ImageBlock())], blank=True)
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS,
        verbose_name="Corps de texte",
        blank=True,
    )
    commentaire = RichTextField(blank=True)

    def build_streamfield_from_legacy_data(self):
        if not self.legacy_produit and not self.legacy_synonyme and not self.infotri:
            # TODO: test
            return

        legacy_produit_or_synonyme = None
        infotri = None
        if self.legacy_produit:
            legacy_produit_or_synonyme = self.legacy_produit
            infotri = self.legacy_produit.infotri

        if self.legacy_synonyme:
            legacy_produit_or_synonyme = self.legacy_synonyme
            infotri = self.legacy_synonyme.produit.infotri

        if infotri is not None:
            self.infotri = [
                ("image", {"image": block.value, "decorative": True})
                for block in infotri
            ]

        if legacy_produit_or_synonyme is not None:
            tabs = []
            if text := legacy_produit_or_synonyme.mauvais_etat:
                tabs.append(
                    ("tabs", {"title": "Mauvais état", "content": [("text", text)]}),
                )

            if text := legacy_produit_or_synonyme.bon_etat:
                tabs.append(
                    ("tabs", {"title": "Bon état", "content": [("text", text)]}),
                )

            if len(tabs) > 0:
                self.body = [("tabs", tabs), *self.body]

        self.save_revision()

    content_panels = Page.content_panels + [
        FieldPanel("infotri"),
        FieldPanel("body"),
    ]

    migration_panels = [
        HelpPanel(
            content=mark_safe(
                "Ces champs serviront à la migration d'un produit ou synonyme"
                "vers la nouvelle approche. <br/>"
                "<ol><li>1. Sélectionner un produit OU synonyme ci-dessous</li>"
                "<li>2. Choisir <b>Migrer les produits/synonymes</b> dans la liste en"
                "cliquant sur le bouton vert en bas à gauche</li>"
                "<li>3. Vérifier les champs après le rechargement de la page</li>"
                "<li>4. Publier la page courante</li></ol>",
            ),
        ),
        FieldPanel("legacy_produit"),
        FieldPanel("legacy_synonyme"),
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
        InlinePanel("synonymes"),
        MultiFieldPanel(
            [
                FieldPanel("usage_unique"),
                FieldPanel("tags"),
                FieldPanel("sous_categorie_objet"),
            ],
            heading="Taxonomie",
        ),
        MultiFieldPanel(
            [
                FieldPanel("bonus"),
                FieldPanel("disable_bonus_inheritance"),
            ],
            heading="Bonus",
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

    search_fields = [
        index.AutocompleteField("title"),
        index.RelatedFields("synonymes", [index.AutocompleteField("nom")]),
    ]

    class Meta:
        verbose_name = "Produit"
        constraints = [
            CheckConstraint(
                condition=Q(legacy_produit__isnull=True)
                | Q(legacy_synonyme__isnull=True),
                name="no_produit_and_synonyme_filled_in_parallel",
            ),
        ]


class FamilyPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "qfdmd.FamilyPage",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )


class FamilyPage(ProduitPage):
    subpage_types = ["qfdmd.produitpage", "qfdmd.synonymepage"]

    class Meta:
        verbose_name = "Famille"


@register_snippet
class TemporarySynonymeModel(TimestampedModel, index.Indexed):
    nom = models.CharField(max_length=255, unique=True)
    page = ParentalKey(
        "wagtailcore.page",
        on_delete=models.CASCADE,
        related_name="synonymes",
    )

    @cached_property
    def famille(self):
        return self.page.specific.famille

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Synnoyme de recherche"
        verbose_name_plural = "Synonymes de recherche"

    panels = [FieldPanel("nom")]

    search_fields = [
        index.AutocompleteField("nom"),
        index.SearchField("nom"),
        index.FilterField("page"),
    ]


class SynonymePage(
    CompiledFieldMixin,
    Page,
    AncestorFieldsMixin,
    TitleFields,
):
    parent_page_types = ["qfdmd.produitpage", "qfdmd.familypage"]

    def get_template(self, request, *args, **kwargs):
        return self.get_parent().specific.template

    def get_context(self, request, *args, **kwargs):
        """
        Extend the default Wagtail page context for SynonymePage.

        This method overrides the default `get_context` behavior in order to
        adjust how templates see the `page` object. By default, `page` would
        refer to the current `SynonymePage`, but synonymes are meant to act
        as "aliases" for their parent page (either a `ProduitPage` or
        `FamilyPage`).

        This makes it possible to render templates as if the parent page were
        being visited directly, while still preserving access to the synonyme
        itself.
        """
        context = super().get_context(request, *args, **kwargs)
        page = context.pop("page")
        context.update(page=self.get_parent().specific, synonyme=page)
        return context

    class Meta:
        verbose_name = "Synonyme de recherche"
        verbose_name_plural = "Synonymes de recherche"

    content_panels = [
        HelpPanel(
            "Cette page est un synonyme de recherche, si vous souhaitez modifier des"
            " champs sur cette page il faut modifier la page parente.",
        ),
        FieldPanel("titre_phrase"),
    ] + Page.content_panels


# LEGACY MODELS
# ==============
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
        ordering = ("-modifie_le",)


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

    id = models.IntegerField(
        primary_key=True,
        help_text="Correspond à l'identifiant ID défini dans les données "
        "<i>Que Faire</i>.",
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

    search_fields = Page.search_fields + [
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
            "first_dir": "jai",
            "limit": 25,
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
            "components/produit/_en_savoir_plus.html",
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


@register_snippet
class Synonyme(index.Indexed, AbstractBaseProduit):
    slug = AutoSlugField(populate_from=["nom"], max_length=255)
    nom = models.CharField(blank=True, unique=True, help_text="Nom du produit")
    produit = models.ForeignKey(
        Produit,
        related_name="synonymes",
        on_delete=models.CASCADE,
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

    def get_url_carte(self, actions=None, map_container_id=None):
        carte_settings = self.produit.carte_settings
        if actions:
            carte_settings.update(
                action_list=actions,
                action_displayed=actions,
            )

        if map_container_id:
            carte_settings.update(
                map_container_id=map_container_id,
            )

        params = urlencode(carte_settings)
        url = reverse("qfdmd:carte", args=[self.slug])
        return f"{url}?{params}"

    @cached_property
    def url_carte(self):
        return self.get_url_carte(None, "carte")

    @cached_property
    def url_carte_mauvais_etat(self):
        actions = "reparer|trier"
        return self.get_url_carte(actions, "mauvais_etat")

    @cached_property
    def url_carte_bon_etat(self):
        actions = "preter|louer|mettreenlocation|donner|echanger|revendre"
        return self.get_url_carte(actions, "bon_etat")

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
        index.AutocompleteField("nom"),
        index.SearchField("id"),
    ]


class Suggestion(models.Model):
    produit = models.OneToOneField(Synonyme, primary_key=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.produit)


@register_setting
class EmbedSettings(BaseGenericSetting):
    backlink_assistant = RichTextField("Backlink de l'iframe de l'assistant")
    backlink_carte = RichTextField("Backlink de l'iframe de la carte")
    backlink_formulaire = RichTextField("Backlink de l'iframe du formulaire")

    class Meta:
        verbose_name = "Réglage des iframes"

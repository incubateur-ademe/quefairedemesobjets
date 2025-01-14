import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.gis.db import models
from django.db.models.functions import Now
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.functional import cached_property
from django_extensions.db.fields import AutoSlugField

logger = logging.getLogger(__name__)


class AbstractBaseProduit(models.Model):
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())
    # Le nom des champs conserve ici délibérément l'ancienne nomenclature,
    # car le travail sur le nommage n'a pas encore été effectué.
    # TODO : renommer ces champs lorsque le métier + technique seront tombés
    # d'accord sur un nom pour ces champs
    qu_est_ce_que_j_en_fais_mauvais_etat = models.TextField(
        blank=True, help_text="Qu'est-ce que j'en fais ? - Mauvais état"
    )
    # TODO : idem ci-dessus
    qu_est_ce_que_j_en_fais_bon_etat = models.TextField(
        blank=True, help_text="Qu'est-ce que j'en fais ? - Bon état"
    )
    comment_les_eviter = models.TextField(
        blank=True, help_text="Comment consommer responsable ?"
    )
    que_va_t_il_devenir = models.TextField(
        blank=True, help_text="Que va-t-il devenir ?"
    )

    class Meta:
        abstract = True
        ordering = ("-modifie_le",)


class Produit(AbstractBaseProduit):
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
        blank=True, help_text="Qu'est-ce que j'en fais ? - ANCIEN CHAMP."
    )
    nom_eco_organisme = models.CharField(blank=True, help_text="Nom de l’éco-organisme")
    filieres_rep = models.CharField(blank=True, help_text="Filière(s) REP concernée(s)")
    slug = models.CharField(blank=True, help_text="Slug - ne pas modifier")

    def __str__(self):
        return f"{self.id} - {self.nom}"

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
            return

        _, _, mauvais_etat_and_rest = text.partition("<b>En bon état</b>")
        mauvais_etat, _, bon_etat = mauvais_etat_and_rest.partition(
            "<b>En mauvais état</b>"
        )

        return (bon_etat, mauvais_etat)

    @property
    def carte_settings(self):
        # TODO : gérer plusieurs catégories ici
        sous_categorie = self.sous_categories.filter(afficher_carte=True).first()
        if not sous_categorie:
            return {}

        return {
            "carte": 1,
            "direction": "jai",
            "first_dir": "jai",
            "limit": 25,
            "sc_id": sous_categorie.id,
        }

    def get_url_carte(self, actions=None):
        carte_settings = self.carte_settings
        if actions:
            carte_settings.update(
                action_list=actions,
                action_displayed=actions,
            )
        params = urlencode(carte_settings)
        return f"{settings.BASE_URL}/?{params}"

    @cached_property
    def url_carte_mauvais_etat(self):
        actions = "reparer|trier"
        return self.get_url_carte(actions)

    @cached_property
    def url_carte_bon_etat(self):
        actions = "preter|emprunter|louer|mettreenlocation|donner|echanger|revendre"
        return self.get_url_carte(actions)

    @cached_property
    def en_savoir_plus(self):
        produit_liens = (
            ProduitLien.objects.filter(produit=self)
            .select_related("lien")
            .order_by("poids")
        )

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
                    "id": "Comment consommer responsable ?",
                    "title": "Comment consommer responsable ?",
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
                    "content": self.en_savoir_plus,
                },
            ]
            if item["content"]
        ]


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


class Synonyme(AbstractBaseProduit):
    slug = AutoSlugField(populate_from=["nom"])
    nom = models.CharField(blank=True, unique=True, help_text="Nom du produit")
    produit = models.ForeignKey(
        Produit, related_name="synonymes", on_delete=models.CASCADE
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
        "Description lue et affichée par les moteurs de recherche.", blank=True
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


class Suggestion(models.Model):
    produit = models.OneToOneField(Synonyme, primary_key=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.produit)


class CMSPage(models.Model):
    id = models.IntegerField(
        primary_key=True,
        help_text="Ce champ est le seul contribuable.<br>"
        "Il correspond à l'ID de la page Wagtail.<br>"
        "Tous les autres champs seront automatiquement contribués à l'enregistrement"
        "de la page dans l'administration Django.",
    )
    body = models.JSONField(default=dict)
    search_description = models.CharField(default="")
    seo_title = models.CharField(default="")
    title = models.CharField(default="")
    slug = models.CharField(default="")
    poids = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        fields_to_fetch_from_api_response = [
            "body",
            "title",
        ]

        fields_to_fetch_from_api_response_meta = [
            "search_description",
            "slug",
            "seo_title",
        ]

        try:
            wagtail_response = requests.get(
                f"{settings.CMS_BASE_URL}/api/v2/pages/{self.id}"
            )
            wagtail_response.raise_for_status()
            wagtail_page_as_json = wagtail_response.json()

            for field in fields_to_fetch_from_api_response:
                if value := wagtail_page_as_json.get(field):
                    setattr(self, field, value)

            for field in fields_to_fetch_from_api_response_meta:
                if value := wagtail_page_as_json["meta"].get(field):
                    setattr(self, field, value)

        except requests.exceptions.RequestException as exception:
            logger.error(f"Error fetching data from CMS API: {exception}")

        super().save(*args, **kwargs)

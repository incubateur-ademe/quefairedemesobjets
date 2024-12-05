from urllib.parse import urlencode

from django.conf import settings
from django.contrib.gis.db import models
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.functional import cached_property
from django_extensions.db.fields import AutoSlugField


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
    qu_est_ce_que_j_en_fais = models.TextField(
        blank=True, help_text="Qu'est-ce que j'en fais ? - ANCIEN CHAMP."
    )
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
    nom_eco_organisme = models.TextField(blank=True, help_text="Nom de l’éco-organisme")
    filieres_rep = models.TextField(blank=True, help_text="Filière(s) REP concernée(s)")
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

    @cached_property
    def mauvais_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_mauvais_etat:
            return self.qu_est_ce_que_j_en_fais_mauvais_etat
        try:
            return self.get_etats_descriptions()[0]
        except KeyError:
            return ""

    @property
    def carte_settings(self):
        # TODO : gérer plusieurs catégories ici
        sous_categorie = self.sous_categories.filter(afficher_carte=True).first()
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
    def bon_etat(self) -> str:
        if self.qu_est_ce_que_j_en_fais_bon_etat:
            return self.qu_est_ce_que_j_en_fais_bon_etat

        try:
            return self.get_etats_descriptions()[1]
        except KeyError:
            return ""

    @cached_property
    def en_savoir_plus(self):
        return render_to_string(
            "components/produit/_en_savoir_plus.html", {"produit": self}
        )

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

    def get_absolute_url(self) -> str:
        return reverse("qfdmd:synonyme-detail", args=[self.slug])

    def __str__(self) -> str:
        return self.nom


class Suggestion(models.Model):
    produit = models.OneToOneField(Synonyme, primary_key=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.produit)

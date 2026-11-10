"""The consignes of a fiche, per geste: from its grid of consignes when it has
one, from the static blocks below otherwise."""

import re
from typing import TypedDict
from urllib.parse import urlencode

from assistant.parcours import Parcours
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from qfdmd.blocks import ETAT_CHOICES
from qfdmd.models import ProduitPage
from qfdmo.models.action import Action, GroupeAction
from wagtail.rich_text import expand_db_html


class Badge(TypedDict):
    condition: str
    libelle: str


class Consigne(TypedDict, total=False):
    """A block of the fiche; `sans_carte`: no map on the site, so no solution
    to send to."""

    code: str
    gestes: list[str]
    libelle: str
    consigne: str
    badges: list[Badge]
    url: str
    localise: bool
    sans_carte: bool


ETATS = dict(ETAT_CHOICES)
EXCLUDED_GROUPES = {"emprunter_preter_louer"}

# A rich text link to a page, as Wagtail stores it: `<a linktype="page" id="3">`.
PAGE_LINK = re.compile(r"<a\b[^>]*\blinktype=\"page\"[^>]*>")
PAGE_ID = re.compile(r"\bid=\"(\d+)\"")
# Anchors Wagtail expanded, still bound to the fiche frame.
FRAMED_LINK = re.compile(r"<a\b(?![^>]*data-turbo-frame)")

#### Assistant V2 : parcours (accueil, fiche, solutions, carte) #3576
# FIXME : dommage qu'on ne puisse pas utilisé le champ order dans GroupeAction
# à voir si on peut changer l'ordre pour tout le monde et se baser sur
# le champ order de GroupeAction
GESTES_ORDER = (
    "reparer",
    "donner_echanger_rapporter",
    "vendre_acheter",
    "emprunter_preter_louer",
    "trier",
)

#### Assistant V2 : parcours (accueil, fiche, solutions, carte) #3576
# FIXME : ça ressemble quand même pas mal à une structure à conserver en DB ?
# gestes = list[GroupeAction.code] -> du coup, est-ce bie nommé
BLOCKS = (
    {
        "code": "reparer",
        "gestes": ("reparer",),
        "libelle": "Réparer",
        "etat": "reparable",
        "bonus": True,
        "consigne": (
            "Votre objet est abîmé mais réparable ? La réparation prolonge sa"
            " durée de vie et coûte souvent moins cher qu'un remplacement. Les"
            " réparateurs proposant le Bonus Réparation sont signalés par le"
            " symbole %."
        ),
    },
    {
        "code": "donner_revendre",
        "gestes": ("donner_echanger_rapporter", "vendre_acheter"),
        "libelle": "Donner ou revendre",
        "etat": "bon_etat",
        "bonus": False,
        "consigne": (
            "Votre objet fonctionne encore et peut servir à quelqu'un d'autre ?"
            " Proposez-le à un proche, donnez-le à une association ou à une"
            " structure de réemploi. Vous pouvez aussi essayer de le revendre"
            " sur une plateforme de seconde main ou en dépôt-vente."
        ),
    },
    {
        "code": "trier",
        "gestes": ("trier",),
        "libelle": "Déposer",
        "etat": "mauvais_etat",
        "bonus": False,
        "consigne": (
            "Votre objet est hors d'usage ? Il ne se jette pas avec les ordures"
            " ménagères : déposez-le en point de collecte pour qu'il soit recyclé"
            " ou traité correctement."
        ),
    },
)


def block_for(gestes) -> dict | None:
    """The block whose gestes are exactly these, whatever their order."""
    wanted = frozenset(gestes)
    return next(
        (block for block in BLOCKS if frozenset(block["gestes"]) == wanted), None
    )


def consignes_for(
    produit_page: ProduitPage | None, parcours: Parcours | None = None
) -> list[Consigne]:
    """Blocks of the fiche, each with the link to its solutions, which carries
    the objet and the address of the `parcours`."""
    base = parcours.as_params() if parcours else {}
    if produit_page is not None and getattr(produit_page, "slug", None):
        base = {**base, "fiche": produit_page.slug}
    localise = bool(parcours and parcours.is_located)

    sans_carte = produit_page is not None and not _shows_map(produit_page)

    cms = produit_page.consignes if produit_page is not None else []
    if cms:
        groupes = _groupes_by_action(cms)
        blocks = (_from_cms(child, groupes, base, localise) for child in cms)
    else:
        known = set(GroupeAction.objects.values_list("code", flat=True))
        blocks = (_from_static(static, known, base, localise) for static in BLOCKS)
    return [{**block, "sans_carte": sans_carte} for block in blocks if block]


def _shows_map(produit_page: ProduitPage) -> bool:
    return any(b["type"] == "carte" for b in produit_page.body.get_prep_value())


def _solutions_url(gestes, base) -> str:
    params = urlencode({**base, "geste": gestes}, doseq=True)
    return f"{reverse('assistant:solutions')}?{params}"


def _from_static(block, known, base, localise) -> Consigne | None:
    gestes = [code for code in block["gestes"] if code in known]
    if not gestes:
        return None

    badges = [{"condition": block["etat"], "libelle": ETATS[block["etat"]]}]
    if block["bonus"]:
        badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

    #### Assistant V2 : parcours (accueil, fiche, solutions, carte) #3576
    # FIXME : pb de linter ?
    #   For the code present, we get this error:
    #   ```
    #   Expression of type "dict[str, Unknown | list[Unknown] | list[dict[str, Unknown]] | str]" is incompatible with return type "Consigne | None"
    #     Type "dict[str, Unknown | list[Unknown] | list[dict[str, Unknown]] | str]" is incompatible with type "Consigne | None"
    #       "dict[str, Unknown | list[Unknown] | list[dict[str, Unknown]] | str]" is incompatible with "Consigne"
    #       "dict[str, Unknown | list[Unknown] | list[dict[str, Unknown]] | str]" is incompatible with "None"
    #   ```
    #   Fix it, verify, and then give a concise explanation. @webapp/assistant/consignes.py:151-154
    return {
        "code": block["code"],
        "gestes": gestes,
        "libelle": block["libelle"],
        "consigne": block["consigne"],
        "badges": badges,
        "url": _solutions_url(gestes, base),
        "localise": localise,
    }


def _from_cms(child, groupes, base, localise) -> Consigne | None:
    """A consigne of the grid, in the shape of the static blocks: its Action
    codes become GroupeAction codes, once each, in the order of the actions."""
    value = child.value
    gestes = list(
        dict.fromkeys(groupes[code] for code in value["gestes"] if code in groupes)
    )
    if not gestes:
        return None

    badges = []
    if value["etat"]:
        badges.append(
            {"condition": value["etat"], "libelle": ETATS.get(value["etat"], "")}
        )
    if value["lieu_de_depot"]:
        badges.append(
            {"condition": "lieu_de_depot", "libelle": value["lieu_de_depot"].libelle}
        )
    if value["bonus_reparation"]:
        badges.append({"condition": "bonus", "libelle": "Bonus Réparation"})

    return {
        "code": child.id,
        "gestes": gestes,
        "libelle": value["titre"],
        "consigne": _consigne_html(value["contenu"].source, base),
        "badges": badges,
        "url": _solutions_url(gestes, base),
        "localise": localise,
    }


def _groupes_by_action(cms) -> dict[str, str]:
    """GroupeAction code of every Action of the grid, prêter / louer excluded
    (no consigne explains them yet, but a grid may still list them)."""
    codes = {code for child in cms for code in child.value["gestes"]}
    return dict(
        Action.objects.filter(code__in=codes, groupe_action__isnull=False)
        .exclude(groupe_action__code__in=EXCLUDED_GROUPES)
        .values_list("code", "groupe_action__code")
    )


def _consigne_html(source, base) -> str:
    """The consigne's links, made to work from the fiche frame: a link to
    another fiche opens it in the assistant, the address kept; any other link
    opens in a new tab. Left as is, Turbo would look for the `assistant-fiche`
    frame in a page of the site and show « Content missing »."""
    ids = {int(PAGE_ID.search(tag).group(1)) for tag in PAGE_LINK.findall(source)}
    fiches = ProduitPage.objects.live().in_bulk(ids) if ids else {}
    location = {k: v for k, v in base.items() if k not in ("fiche", "objet")}

    def to_fiche(match):
        page = fiches.get(int(PAGE_ID.search(match.group(0)).group(1)))
        if page is None:
            return match.group(0)
        params = urlencode({**location, "fiche": page.slug, "objet": page.title})
        url = f"{reverse('assistant:produit', args=[page.slug])}?{params}"
        return f'<a href="{escape(url)}" data-turbo-frame="_top">'

    html = expand_db_html(PAGE_LINK.sub(to_fiche, source))
    return mark_safe(
        FRAMED_LINK.sub(
            '<a target="_blank" rel="noopener" data-turbo-frame="_top"', html
        )
    )

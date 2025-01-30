from django.db.models import Q
from utils.django import django_setup_full

django_setup_full()

from qfdmd.models import Lien  # noqa: E402
from qfdmo.models import DisplayedActeur  # noqa: E402

URL_TYPES_TO_MODEL = {
    "qfdmo_displayedacteur.url": DisplayedActeur,
    "qfdmd_lien.url": Lien,
}
URL_TYPES_TO_PK = {
    "qfdmo_displayedacteur.url": "identifiant_unique",
    "qfdmd_lien.url": "id",
}
URL_TYPES_TO_EXTRA_FIELDS = {
    "qfdmo_displayedacteur.url": ["nom"],
    "qfdmd_lien.url": ["titre_du_lien"],
}


def crawl_urls_select_from_db(url_type: str, limit: int = 50) -> list[dict]:
    if url_type not in URL_TYPES_TO_MODEL:
        raise ValueError(f"{url_type=} invalide: doit être {URL_TYPES_TO_MODEL.keys()}")

    model = URL_TYPES_TO_MODEL[url_type]
    pk = URL_TYPES_TO_PK[url_type]
    extra_fields = URL_TYPES_TO_EXTRA_FIELDS[url_type]
    # TODO: move query above and add statut=ACTIF if acteur
    entries = (
        model.objects.filter(Q(url__isnull=False) & ~Q(url__exact=""))
        .order_by("url")
        .values(pk, "url", *extra_fields)[:limit]
    )
    return list(entries)

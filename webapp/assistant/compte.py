"""Number of places offering some gestes near a point.

Fetched by the fiche *after* it renders, through `/api/v1/lieux/compte`:
counting costs up to half a second on a large objet (ADR 0010), far beyond
the page's budget, so the page never waits for it. The result is cached 12 h
per gestes, objet and ~1 km cell, the same lifetime as the offers cache: the
data only moves with the imports.
"""

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache

from qfdmo.models.acteur import DisplayedActeur

# "À proximité": the 20 km the spec mentions as the map's maximum radius (#3356).
RADIUS_KM = 20
COUNT_CACHE_TTL = 60 * 60 * 12
# Two decimals: about a kilometre. The counter is approximate by design
# (ADR 0010): neighbours a street apart share one entry.
COORDINATE_PRECISION = 2


def count_nearby(gestes, sous_categorie_ids, longitude, latitude) -> int:
    cell = (
        round(longitude, COORDINATE_PRECISION),
        round(latitude, COORDINATE_PRECISION),
    )
    key = "compte:{}:{}:{}:{}".format(
        ",".join(sorted(gestes)),
        ",".join(map(str, sorted(sous_categorie_ids))),
        cell[0],
        cell[1],
    )
    count = cache.get(key)
    if count is None:
        count = _count(gestes, sous_categorie_ids, cell)
        cache.set(key, count, COUNT_CACHE_TTL)
    return count


def _count(gestes, sous_categorie_ids, cell) -> int:
    center = Point(cell[0], cell[1], srid=4326)
    return (
        DisplayedActeur.objects.all()
        .proposing(gestes, sous_categorie_ids)
        .physical()
        .filter(location__dwithin=(center, D(km=RADIUS_KM)))
        .count()
    )

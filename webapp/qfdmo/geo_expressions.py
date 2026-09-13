from django.db.models import FloatField, Func, Value


class NearestTo(Func):
    """Ordonne par l'opérateur KNN `<->` de PostGIS.

    Distinct de `Distance` : l'opérateur KNN permet à PostgreSQL de parcourir
    l'index GiST dans l'ordre des distances croissantes et de s'arrêter au
    LIMIT, au lieu de calculer la distance de tous les candidats puis de les
    trier. Mesuré sur 388 000 acteurs : 2 ms contre 437 ms à Paris.

    La valeur produite sert au tri, pas à l'affichage. Annoter `Distance` en
    parallèle si la distance exacte doit être montrée.
    """

    template = "%(expressions)s"
    arg_joiner = " <-> "
    output_field = FloatField()

    def __init__(self, field_name: str, point):
        wkt = Value(f"SRID={point.srid};POINT({point.x} {point.y})")
        super().__init__(field_name, Func(wkt, template="%(expressions)s::geography"))

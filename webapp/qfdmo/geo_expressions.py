from django.db.models import FloatField, Func, Value


class NearestTo(Func):
    """Orders by the PostGIS KNN operator `<->`.

    Distinct from `Distance`: the KNN operator lets PostgreSQL walk the GiST
    index in increasing distance order and stop at the LIMIT, instead of
    computing the distance of every candidate and then sorting. Measured on
    388,000 acteurs: 2 ms against 437 ms in Paris.

    The produced value is meant for sorting, not display. Annotate `Distance`
    alongside if the exact distance must be shown.
    """

    template = "%(expressions)s"
    arg_joiner = " <-> "
    output_field = FloatField()

    def __init__(self, field_name: str, point):
        wkt = Value(f"SRID={point.srid};POINT({point.x} {point.y})")
        super().__init__(field_name, Func(wkt, template="%(expressions)s::geography"))

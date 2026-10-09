from django.db.models import QuerySet


def paginate(queryset: QuerySet, page: int, page_size: int) -> tuple[list, int]:
    """Returns (items of the page, total). `page` starts at 1."""
    total = queryset.count()
    offset = (page - 1) * page_size
    return list(queryset[offset : offset + page_size]), total

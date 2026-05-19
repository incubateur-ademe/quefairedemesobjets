from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def with_query(url: str, key: str, value: str) -> str:
    """Return ``url`` with the query parameter ``key`` set to ``value``.

    Replaces any existing occurrence of ``key`` (including duplicates) and
    preserves the order of other parameters. Keeps the path, fragment, and
    scheme intact.
    """
    parts = urlsplit(url)
    pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != key
    ]
    pairs.append((key, value))
    return urlunsplit(parts._replace(query=urlencode(pairs)))

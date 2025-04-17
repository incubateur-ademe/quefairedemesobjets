from typing import Any


def dicts_get_nested_key(d: dict, path: str) -> Any:
    """Utility to access a nested key in a dictionary
    via dot notation (e.g. "key1.key2.key3")"""
    keys = path.split(".")
    for key in keys:
        d = d.get(key)  # type: ignore
    return d

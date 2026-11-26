"""Tests for the QFDMO tag whitelist inside the osm2pgsql Lua style config.

The Lua file runs inside osm2pgsql at import time, not in the Python test
suite. Re-importing the full France PBF is expensive, so this test is the
cheap safeguard available to catch a typo that would silently drop (or
re-introduce) an entire category in the whitelist.
"""

import re
from pathlib import Path

LUA_FILEPATH = (
    Path(__file__).resolve().parents[3] / "osm" / "config" / "osm_2_pgsql.lua"
)

# Inside the Lua source, the only quoted strings containing a "=" are the
# "key=value" entries of the `relevant_tag_values` whitelist.
WHITELIST_ENTRY_RE = re.compile(r'"([a-z0-9_]+=[a-z0-9_]+)"')

# Categories deliberately excluded from the whitelist (out of QFDMO scope,
# or else the previous key-based filter imported ~57M mostly irrelevant rows).
FORBIDDEN_PREFIXES = (
    "building=",
    "healthcare=",
    "landuse=",
    "leisure=",
    "office=",
    "telecom=",
    "tourism=",
)

REQUIRED_ENTRIES = {
    # Drop-off / recycling / donation (broad scope, incl. PAV & déchèteries)
    "amenity=recycling",
    "amenity=givebox",
    # Repair / second-hand / reuse shops
    "shop=bicycle",
    "shop=second_hand",
    "shop=charity",
    # Repair craftspeople
    "craft=shoe_repair",
    # Rental
    "amenity=bicycle_rental",
}


def test_lua_file_exists():
    assert LUA_FILEPATH.exists()


def test_whitelist_entries_are_well_formed_and_unique():
    entries = WHITELIST_ENTRY_RE.findall(LUA_FILEPATH.read_text())
    assert entries, "no whitelist entry found in osm_2_pgsql.lua"
    assert len(entries) == len(set(entries)), "duplicated whitelist entries"
    assert all(
        entry == entry.lower() for entry in entries
    ), "whitelist entries must be lowercase"


def test_no_bare_key_or_noise_key_entries():
    entries = WHITELIST_ENTRY_RE.findall(LUA_FILEPATH.read_text())
    assert all(
        len(entry.split("=", 1)[1]) for entry in entries
    ), "whitelist entries must carry a tag value (key=value)"
    assert not any(
        entry.startswith(FORBIDDEN_PREFIXES) for entry in entries
    ), "a deliberately excluded key was whitelisted"


def test_required_categories_present():
    entries = set(WHITELIST_ENTRY_RE.findall(LUA_FILEPATH.read_text()))
    missing = REQUIRED_ENTRIES - entries
    assert not missing, f"missing whitelist entries: {sorted(missing)}"

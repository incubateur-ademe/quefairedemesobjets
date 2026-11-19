from types import SimpleNamespace

import pytest

from core.templatetags.custom_dsfr_tags import (
    accordions_heading_tag,
    only_tiles,
    shift_headings,
)


class TestShiftHeadings:
    @pytest.mark.parametrize(
        "tag, expected",
        [
            ("h2", "<h3>A</h3><p>x</p><h4 class='y'>B</h4>"),
            ("h3", "<h4>A</h4><p>x</p><h5 class='y'>B</h5>"),
        ],
    )
    def test_shifts_below_the_given_tag(self, tag, expected):
        html = "<h2>A</h2><p>x</p><h3 class='y'>B</h3>"

        assert shift_headings(html, tag) == expected

    def test_stops_at_h6(self):
        assert shift_headings("<h5>A</h5>", "h3") == "<h6>A</h6>"

    def test_leaves_other_tags_alone(self):
        assert (
            shift_headings("<hr><header>x</header>", "h2") == "<hr><header>x</header>"
        )


class TestAccordionsHeadingTag:
    def test_h3_under_a_group_title(self):
        blocks = [SimpleNamespace(block_type="title")]

        assert accordions_heading_tag(blocks) == "h3"

    def test_h2_without_group_title(self):
        blocks = [SimpleNamespace(block_type="accordion")]

        assert accordions_heading_tag(blocks) == "h2"


class TestOnlyTiles:
    def test_true_when_every_block_is_a_tile(self):
        blocks = [SimpleNamespace(block_type="tile")] * 2

        assert only_tiles(blocks) is True

    def test_false_when_mixed_or_empty(self):
        assert only_tiles([SimpleNamespace(block_type="text")]) is False
        assert only_tiles([]) is False

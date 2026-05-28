from core.url_utils import with_query


class TestWithQuery:
    def test_appends_param_when_missing(self):
        assert with_query("/carte/foo", "view_mode-view", "liste") == (
            "/carte/foo?view_mode-view=liste"
        )

    def test_replaces_existing_param(self):
        result = with_query(
            "/carte/foo?view_mode-view=carte", "view_mode-view", "liste"
        )
        assert result == "/carte/foo?view_mode-view=liste"

    def test_preserves_other_params_and_order(self):
        result = with_query("/carte/foo?a=1&b=2", "view_mode-view", "liste")
        assert result == "/carte/foo?a=1&b=2&view_mode-view=liste"

    def test_drops_duplicate_keys(self):
        result = with_query(
            "/carte/foo?view_mode-view=carte&view_mode-view=other&a=1",
            "view_mode-view",
            "liste",
        )
        assert result == "/carte/foo?a=1&view_mode-view=liste"

    def test_preserves_fragment(self):
        result = with_query("/carte/foo?a=1#anchor", "view_mode-view", "liste")
        assert result == "/carte/foo?a=1&view_mode-view=liste#anchor"

    def test_url_encodes_value(self):
        result = with_query("/carte/foo", "q", "hello world")
        assert result == "/carte/foo?q=hello+world"

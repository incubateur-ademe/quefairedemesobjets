import pandas as pd
import pytest
from crawl.tasks.business_logic.candidates.groupby_url import (
    crawl_urls_candidates_groupby_url,
)
from rich import print


class TestCrawlUrlsGroupbyUrl:

    @pytest.fixture
    def df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "url": ["url1", "url2", "url1"],
                "nom": ["Acteur 1", "Acteur 1", "Acteur 2"],
                "statut": ["ACTIF", "ACTIF", "ACTIF"],
                "foo": ["bar", "baz", "qux"],
            }
        )

    @pytest.fixture
    def working(self, df) -> pd.DataFrame:
        df = crawl_urls_candidates_groupby_url(
            df, col_groupby="url", col_grouped_data="acteurs"
        )
        print(df.to_dict(orient="records"))
        return df

    def test_structure(self, working):
        # We only keep the URL column, everything else
        # goes into a list of dictionaries
        assert working.columns.tolist() == ["url", "acteurs"]
        assert all(isinstance(x, list) for x in working["acteurs"])

    def test_dicts_contain_all_columns(self, working):
        # With the "foo" column which doesn't belong to
        # acteurs we show that everything is bundled
        # into the grouped_data: we could change behaviour to
        # only including acteur data but at least we
        # have behaviour tested & locked for now
        dic1 = working["acteurs"][0][0]
        assert sorted(dic1.keys()) == sorted(["nom", "statut", "foo"])

    def test_urls_properly_grouped(self, working):
        assert working["url"].tolist() == ["url1", "url2"]

    def test_dicts_properly_grouped(self, working):
        list1 = working["acteurs"][0]
        assert len(list1) == 2
        assert list1[0]["nom"] == "Acteur 1"
        assert list1[1]["nom"] == "Acteur 2"

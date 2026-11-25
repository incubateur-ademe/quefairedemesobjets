# python -m pytest scripts/infrastructure/test_delete_old_images.py
from delete_old_images import tags_to_delete


def names(tags):
    return [tag["name"] for tag in tags]


def test_keeps_recent_tags_and_those_that_may_run_in_prod():
    tags = [
        {"name": name}
        for name in [
            "sha-9",
            "prod-latest",
            "v3.0.0",
            "sha-8",
            "prod-abc",
            "v2.0.0",
            "sha-7",
            "v1.0.0",
            "sha-6",
        ]
    ]

    assert names(tags_to_delete(tags, tags_to_keep=2)) == ["sha-7", "sha-6"]


def test_protects_only_the_latest_releases():
    tags = [{"name": f"v{n}.0.0"} for n in range(10, 0, -1)]

    assert names(tags_to_delete(tags, tags_to_keep=0)) == [
        "v5.0.0",
        "v4.0.0",
        "v3.0.0",
        "v2.0.0",
        "v1.0.0",
    ]

# For each image in the Paris region of the Scaleway Container Registry,
# keep up `TAGS_TO_KEEP` tags per image. The oldest ones will be deleted first.
# Tags that may run in prod are kept on top of that: the latest
# `PROTECTED_PER_KIND` release tags (v1.2.3), the latest `prod-*` tags and
# every moving `*-latest` tag.
#
# Usage:
# TOKEN="XXXXX" TAGS_TO_KEEP=20 python delete_old_images.py
import logging
import os
import re
from collections import Counter

import requests

REGION = "fr-par"
PROTECTED_PER_KIND = 5

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("delete_old_images")


def protected_kind(tag_name):
    if tag_name.endswith("-latest"):
        return tag_name
    if re.fullmatch(r"v\d+(\.\d+)*", tag_name):
        return "release"
    if tag_name.startswith("prod-"):
        return "prod"
    return None


def tags_to_delete(tags, tags_to_keep):
    """tags: newest first."""
    protected = Counter()
    kept = 0
    to_delete = []
    for tag in tags:
        kind = protected_kind(tag["name"])
        if kind and protected[kind] < PROTECTED_PER_KIND:
            protected[kind] += 1
        elif kept < tags_to_keep:
            kept += 1
        else:
            to_delete.append(tag)
    return to_delete


# See https://www.scaleway.com/en/developers/api/container-registry/
def main():
    headers = {"X-Auth-Token": os.environ["TOKEN"]}
    namespace_id = os.environ["NAMESPACE_ID"]
    tags_to_keep = int(os.environ["TAGS_TO_KEEP"])

    # Fetch images
    url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images?page_size=100&order_by=created_at_asc&namespace_id={namespace_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    images = response.json()["images"]

    to_delete = []
    for image in images:
        logger.info(f"Fetching tags for {image['name']}…")
        url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images/{image['id']}/tags?page_size=100&order_by=created_at_desc"
        response = requests.get(url, headers=headers)
        for tag in tags_to_delete(response.json()["tags"], tags_to_keep):
            logger.info(f"Will delete tag {tag['name']} for image {image['name']}")
            to_delete.append(tag)

    for tag in to_delete:
        url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/tags/{tag['id']}"
        requests.delete(url, headers=headers)


if __name__ == "__main__":
    main()

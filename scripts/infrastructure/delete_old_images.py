# For each image in the Paris region of the Scaleway Container Registry,
# keep up `TAGS_TO_KEEP` tags per image. The oldest ones will be deleted first.
#
# Usage:
# TOKEN="XXXXX" TAGS_TO_KEEP=20 python delete_old_images.py
import urllib.request
import os
import json
import logging

REGION = "fr-par"
TOKEN = os.environ["TOKEN"]
TAGS_TO_KEEP = int(os.environ["TAGS_TO_KEEP"])

headers = {"X-Auth-Token": TOKEN}

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("delete_old_images")


# See https://www.scaleway.com/en/developers/api/container-registry/
def main():
    # Fetch images
    url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images?page_size=100&order_by=created_at_asc"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        res = response.read()
        images = json.loads(res)["images"]

    # Get all tags by image and keep up to `TAGS_TO_KEEP` tags
    tags_to_delete = []
    for image in images:
        logger.info(f"Fetching tags for {image['name']}…")
        url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images/{image['id']}/tags?page_size=100&order_by=created_at_desc"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            res = response.read()
            tags = json.loads(res)["tags"]
        i = 0
        for tag in tags:
            if i < TAGS_TO_KEEP:
                i = i + 1
            else:
                logger.info(f"Will delete tag {tag['name']} for image {image['name']}")
                tags_to_delete.append(tag)

    # Delete tags
    for tag in tags_to_delete:
        url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/tags/{tag['id']}"
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        with urllib.request.urlopen(req) as response:
            res = response.read()


if __name__ == "__main__":
    main()

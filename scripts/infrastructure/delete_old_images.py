# For each image in the Paris region of the Scaleway Container Registry,
# keep up `TAGS_TO_KEEP` tags per image. The oldest ones will be deleted first.
#
# Usage:
# TOKEN="XXXXX" TAGS_TO_KEEP=20 python delete_old_images.py
import logging
import os

import requests

REGION = "fr-par"
TOKEN = os.environ["TOKEN"]
NAMESPACE_ID = os.environ["NAMESPACE_ID"]
TAGS_TO_KEEP = int(os.environ["TAGS_TO_KEEP"])

headers = {"X-Auth-Token": TOKEN}

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("delete_old_images")


# See https://www.scaleway.com/en/developers/api/container-registry/
def main():
    # Fetch images
    url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images?page_size=100&order_by=created_at_asc&namespace_id={NAMESPACE_ID}"
    response = requests.get(url, headers=headers)
    if response.status_code >= 400:
        raise Exception(
            f"Failed to fetch images: {response.status_code} - {response.text}"
        )
    images = response.json()["images"]

    # Get all tags by image and keep up to `TAGS_TO_KEEP` tags
    tags_to_delete = []
    for image in images:
        logger.info(f"Fetching tags for {image['name']}…")
        url = f"https://api.scaleway.com/registry/v1/regions/{REGION}/images/{image['id']}/tags?page_size=100&order_by=created_at_desc"
        response = requests.get(url, headers=headers)
        tags = response.json()["tags"]
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
        response = requests.delete(url, headers=headers)


if __name__ == "__main__":
    main()

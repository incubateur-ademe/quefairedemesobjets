import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def create_new_row_in(database_id, data):
    NOTION_TOKEN = settings.NOTION_TOKEN
    if not NOTION_TOKEN:
        logging.warning("The notion token is not set in local environment")
        return

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": "Sample Row"}}]},
            "Status": {"select": {"name": "In Progress"}},
            "Date": {"date": {"start": "2025-01-15"}},
        },
    }

    response = requests.post(
        "https://api.notion.com/v1/pages", headers=headers, json=payload
    )

    if response.status_code == 200:
        logger.info("Row added successfully!")
    else:
        logger.error(f"Failed to add row:{response.status_code=}, {response.text=}")

import logging

import requests
from django.conf import settings
from django.utils import timezone
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)


class ContactFormData(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


def create_new_row_in_notion_table(database_id: str, data: ContactFormData):
    notion_token = settings.NOTION.get("TOKEN")
    if not notion_token:
        logger.error("The notion token is not set in local environment")
        return

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Nom": {"title": [{"text": {"content": data.name}}]},
            "Email": {"email": data.email},
            "Objet": {"rich_text": [{"text": {"content": data.subject}}]},
            "Message": {"rich_text": [{"text": {"content": data.message}}]},
            "Date": {"date": {"start": timezone.now().isoformat()}},
        },
    }

    response = requests.post(
        "https://api.notion.com/v1/pages", headers=headers, json=payload
    )

    if response.status_code == 200:
        logger.info("New contact form submission")
    else:
        logger.error(f"Failed to add row:{response.status_code=}, {response.text=}")

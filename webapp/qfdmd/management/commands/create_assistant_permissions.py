import logging

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from wagtail.admin.models import Admin

logger = logging.getLogger(__name__)


def create_permissions():
    # Custom permissions
    content_type = ContentType.objects.get_for_model(Admin)
    beta_search_permission = Permission.objects.create(
        content_type=content_type,
        codename="can_see_beta_search",
        name="Peut voir la version beta de la recherche de l'assistant",
    )
    logger.info(f"{beta_search_permission=} created")


class Command(BaseCommand):
    help = "Create permissions required for the Assistant website to work"

    def handle(self, *args, **options):
        create_permissions()

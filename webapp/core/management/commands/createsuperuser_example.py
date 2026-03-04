from django.core.management.base import BaseCommand


from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = "Import legacy synonymes as SearchTags for all ProduitPages "

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            User.objects.create_superuser("admin", password="admin")
        except IntegrityError:
            pass

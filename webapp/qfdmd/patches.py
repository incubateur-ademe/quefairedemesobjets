# sites-conformes 3.x queries a non-existent tag relation (FieldError on catalogs).
# Delete this file when upgrading to 4.x, which fixes it.
from django.db.models import Count, Q
from sites_conformes.content_manager.managers import TagManager

TAG_USAGE_LOOKUP = "sites_conformes_content_manager_tagcontentpage_items"


def tags_with_usecount(self, min_count=0):
    return self.annotate(
        usecount=Count(
            TAG_USAGE_LOOKUP,
            filter=Q(**{f"{TAG_USAGE_LOOKUP}__content_object__live": True}),
            distinct=True,
        )
    ).filter(usecount__gte=min_count)


TagManager.tags_with_usecount = tags_with_usecount

from django.views.decorators.cache import cache_control

CACHE_FIVE_MINUTES = cache_control(public=True, max_age=300, stale_while_revalidate=60)
CACHE_ONE_HOUR = cache_control(public=True, max_age=3600, stale_while_revalidate=300)

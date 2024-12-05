from django.contrib.postgres.lookups import Unaccent
from django.db.models import CharField, TextField

# Useful to support unaccent lookups in django admin, for
# acteurs and produits for example
CharField.register_lookup(Unaccent)
TextField.register_lookup(Unaccent)

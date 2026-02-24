from django.db import models
from django.db.models.functions import Now


class TimestampedModel(models.Model):
    cree_le = models.DateTimeField(auto_now_add=True, db_default=Now())
    modifie_le = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        abstract = True

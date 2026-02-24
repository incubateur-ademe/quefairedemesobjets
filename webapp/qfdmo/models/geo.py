from django.db import models

from qfdmo.geo_api import (
    bbox_from_list_of_geojson,
    retrieve_epci_geojson_from_api_or_cache,
)
from qfdmo.map_utils import compile_frontend_bbox


class EPCIManager(models.Manager):
    def get_bbox_from_epci_codes(self, codes):
        epcis = self.filter(code__in=codes)
        if epcis.exists():
            geojson_list = [
                retrieve_epci_geojson_from_api_or_cache(code) for code in codes
            ]
            bbox = bbox_from_list_of_geojson(geojson_list, buffer=0)
            return compile_frontend_bbox(bbox)
        return None


class EPCI(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=255)

    objects = EPCIManager()

    def __str__(self):
        return f"{self.nom} ({self.code})"

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from qfdmo.models import Acteur
from qfdmo.models.quality import AdresseVerification

GOOGLE_ADDRESS_VALIDATION_API = f"https://addressvalidation.googleapis.com/v1:validateAddress?key={settings.GOOGLE_API_KEY}"


class Command(BaseCommand):
    help = """
using the Google API : https://developers.google.com/maps/documentation/address-validation/requests-validate-address?hl=fr
we can validate the address of the acteur
"""

    def handle(self, *args, **options):
        for acteur in Acteur.objects.order_by("?").all()[:132]:
            if acteur:
                address = [acteur.adresse]
                if acteur.adresse_complement:
                    address.append(acteur.adresse_complement)

                response = requests.post(
                    GOOGLE_ADDRESS_VALIDATION_API,
                    json={
                        "address": {
                            "regionCode": "FR",
                            "postalCode": acteur.code_postal,
                            "locality": acteur.ville,
                            "addressLines": address,
                        }
                    },
                )
                print(response.json())
                new_address = response.json()["result"]["address"]["formattedAddress"]
                result = response.json()["result"]
                print(
                    "old address = "
                    + ", ".join(address)
                    + ", "
                    + acteur.code_postal
                    + " "
                    + acteur.ville
                )
                valid_address = (
                    "addressComplete" in result["verdict"]
                    and result["verdict"]["addressComplete"]
                    and "inputGranularity" in result["verdict"]
                    and result["verdict"]["inputGranularity"]
                    in ["PREMISE", "SUB_PREMISE"]
                    and "validationGranularity" in result["verdict"]
                    and result["verdict"]["validationGranularity"]
                    in ["PREMISE", "SUB_PREMISE"]
                )
                valid_geocode = result["verdict"]["geocodeGranularity"] in [
                    "PREMISE",
                    "SUB_PREMISE",
                ]
                address_lines = (
                    result["address"]["postalAddress"]["addressLines"]
                    if "addressLines" in result["address"]["postalAddress"]
                    else []
                )
                print("new address = " + new_address)
                AdresseVerification.objects.create(
                    acteur=acteur,
                    source="Google Address Verification API",
                    adresse=address_lines[0] if len(address_lines) > 0 else None,
                    adresse_complement=address_lines[1]
                    if len(address_lines) > 1
                    else None,
                    code_postal=result["address"]["postalAddress"]["postalCode"],
                    ville=result["address"]["postalAddress"]["locality"],
                    result=result,
                    adresse_valide=valid_address,
                    latitude=result["geocode"]["location"]["latitude"],
                    longitude=result["geocode"]["location"]["longitude"],
                    geoloc_valide=valid_geocode,
                )


test = {
    "result": {
        "verdict": {
            "inputGranularity": "PREMISE",
            "validationGranularity": "PREMISE",
            "geocodeGranularity": "PREMISE",
            "addressComplete": True,
        },
        "address": {
            "formattedAddress": "23 ***, 66000 Perpignan, France",
            "postalAddress": {
                "regionCode": "FR",
                "languageCode": "fr",
                "postalCode": "66000",
                "locality": "Perpignan",
                "addressLines": ["23 Av. Georges Guynemer"],
            },
            "addressComponents": [
                {
                    "componentName": {"text": "23"},
                    "componentType": "street_number",
                    "confirmationLevel": "CONFIRMED",
                },
                {
                    "componentName": {
                        "text": "***",
                        "languageCode": "fr",
                    },
                    "componentType": "route",
                    "confirmationLevel": "CONFIRMED",
                },
                {
                    "componentName": {"text": "66000"},
                    "componentType": "postal_code",
                    "confirmationLevel": "CONFIRMED",
                },
                {
                    "componentName": {"text": "Perpignan", "languageCode": "fr"},
                    "componentType": "locality",
                    "confirmationLevel": "CONFIRMED",
                },
                {
                    "componentName": {"text": "France", "languageCode": "fr"},
                    "componentType": "country",
                    "confirmationLevel": "CONFIRMED",
                },
            ],
        },
        "geocode": {
            "location": {"latitude": 42.6949013, "longitude": 2.9043527},
            "plusCode": {"globalCode": "8FJ4MWV3+XP"},
            "bounds": {
                "low": {"latitude": 42.6948581, "longitude": 2.9042665},
                "high": {"latitude": 42.694952, "longitude": 2.9044113},
            },
            "featureSizeMeters": 9.022798,
            "placeId": "ChIJbWxWzrZvsBIRJNxj_gRv9qM",
            "placeTypes": ["premise"],
        },
        "metadata": {"business": True, "residential": False},
    },
    "responseId": "4a3e6ebb-d466-4f2f-b3e3-05aebd288d4b",
}

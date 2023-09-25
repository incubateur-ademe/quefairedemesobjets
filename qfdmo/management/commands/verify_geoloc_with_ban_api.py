import csv
import logging

import haversine as hs
import requests
from django.core.management.base import BaseCommand
from haversine import Unit

from qfdmo.models import Acteur

BAN_API_URL = "https://api-adresse.data.gouv.fr/search/?q={}"


class Command(BaseCommand):
    help = """
For each acteur, check the location provided by the BAN API using their address
"""

    def handle(self, *args, **options):
        count_ignore = 0
        count_auto = 0
        count_manuel = 0
        with open("result_geoloc.csv", "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=",")
            writer.writerow(
                [
                    "acteur",
                    "localisation en DB",
                    "localisation par la BAN",
                    "score",
                    "distance",
                    "Gmap itineraire",
                ]
            )
            for acteur in Acteur.objects.all()[:1000]:
                if acteur.adresse:
                    response = requests.get(
                        BAN_API_URL.format(acteur.get_address_for_ban())
                    )

                    if response.status_code == 200:
                        response_json = response.json()
                        if response_json["features"]:
                            feature = response_json["features"][0]
                            point_from_db = acteur.location.coords
                            point_from_ban = tuple(feature["geometry"]["coordinates"])
                            try:
                                distance = hs.haversine(
                                    point_from_db, point_from_ban, unit=Unit.METERS
                                )
                            except:
                                logging.error(
                                    f"Error while calculating distance for {acteur}"
                                    f", cf. location {acteur.location.coords}"
                                )
                                distance = 0
                            todo = None
                            if distance < 10:
                                todo = "ignore"
                            elif acteur.adresse.strip()[0].isnumeric():
                                if feature["properties"]["score"] >= 0.5:
                                    todo = "auto"
                            if todo is None:
                                todo = "manuel"
                            result = {
                                "todo": todo,
                                "acteur": acteur,
                                "adresse": f"{acteur.adresse} {acteur.adresse_complement} {acteur.code_postal} {acteur.ville}",
                                "localisation_db": point_from_db,
                                "localisation_ban": point_from_ban,
                                "score": feature["properties"]["score"],
                                "distance": distance,
                                "gmapitineraire": f"https://www.google.com/maps/dir/?api=1&origin={point_from_db[1]},{point_from_db[0]}&destination={point_from_ban[1]},{point_from_ban[0]}&travelmode=driving",
                            }
                            writer.writerow(result.values())
                            print(acteur, distance)
                            # self.location = Point(
                            #     feature["geometry"]["coordinates"], srid=4326
                        else:
                            logging.error(
                                f"Error while fetching BAN API for {acteur}: {response_json}"
                            )
                    else:
                        logging.error(
                            f"Error while fetching BAN API for {acteur}: {response.status_code}"
                        )
        print("count_ignore", count_ignore)
        print("count_auto", count_auto)
        print("count_manuel", count_manuel)

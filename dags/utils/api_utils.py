from ratelimit import limits, sleep_and_retry
import requests
from importlib import import_module
from pathlib import Path

env = Path(__file__).parent.parent.name

mapping_utils = import_module(f"{env}.utils.mapping_utils")


def fetch_dataset_from_point_apport(url):
    all_data = []
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["results"])
            url = data.get("next", None)
        else:
            print(f"Failed to fetch data: {response.status_code}")
            break
    return all_data


def fetch_data_from_url(base_url):
    if "pointsapport.ademe.fr" in base_url:
        return fetch_dataset_from_point_apport(base_url)
    elif "artisanat.fr" in base_url:
        return fetch_dataset_from_artisanat(base_url)
    return []


def fetch_dataset_from_artisanat(base_url):
    all_data = []
    offset = 0
    total_records = requests.get(base_url, params={"limit": 1, "offset": 0}).json()[
        "total_count"
    ]
    records_per_request = 100
    params = {"limit": records_per_request, "offset": 0}
    while offset < total_records:
        params.update({"offset": offset})
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            all_data.extend(data["results"])
            offset += records_per_request
        else:
            response.raise_for_status()

    return all_data


@sleep_and_retry
@limits(calls=3, period=1)
def call_annuaire_entreprises(query, adresse_query_flag=False):
    params = {"q": query, "page": 1, "per_page": 1, "etat_administratif": "A"}
    base_url = "https://recherche-entreprises.api.gouv.fr"
    endpoint = "/search"
    try:
        response = requests.get(url=f"{base_url}{endpoint}", params=params)
        res = []
        if response.status_code == 200:
            data = response.json()
            if "results" in data and data["results"]:
                data = data["results"][0]
                nombre_etablissements_ouverts = data.get(
                    "nombre_etablissements_ouverts"
                )
                if nombre_etablissements_ouverts == 1 and not adresse_query_flag:
                    # Récupérer les informations du siège
                    siege = data.get("siege", {})
                    adresse_siege = siege.get("adresse")
                    etat_admin_siege = siege.get("etat_administratif")
                    siret_siege = siege.get("siret")
                    categorie_naf_siege = siege.get("activite_principale")
                    nom_candidat = siege.get("nom_commercial") or siege.get(
                        "nom_complet"
                    )
                    latitude = siege.get("latitude")
                    longitude = siege.get("longitude")

                    res.append(
                        {
                            "adresse_candidat": adresse_siege,
                            "etat_admin_candidat": etat_admin_siege,
                            "categorie_naf_candidat": categorie_naf_siege,
                            "siret_candidat": siret_siege,
                            "nom_candidat": nom_candidat,
                            "latitude_candidat": latitude,
                            "longitude_candidat": longitude,
                            "siege_flag": True,
                            "nombre_etablissements_ouver"
                            "ts": nombre_etablissements_ouverts,
                            "search_by_siret_candidat": False,
                        }
                    )
                # Récupérer les informations du premier candidat ouvert
                matching_etablissements = data.get("matching_etablissements", [])
                if matching_etablissements:
                    premier_etablissement = matching_etablissements[0]
                    etat_admin_candidat = premier_etablissement.get(
                        "etat_administratif"
                    )
                    categorie_naf_candidat = premier_etablissement.get(
                        "activite_principale"
                    )
                    siret_candidat = premier_etablissement.get("siret")
                    adresse_candidat = premier_etablissement.get("adresse")
                    nom_candidat = premier_etablissement.get("nom_commercial")
                    latitude = premier_etablissement.get("latitude")
                    longitude = premier_etablissement.get("longitude")
                    search_by_siret_candidat = False
                    if not adresse_query_flag:
                        search_by_siret_candidat = True
                    res.append(
                        {
                            "adresse_candidat": adresse_candidat,
                            "etat_admin_candidat": etat_admin_candidat,
                            "categorie_naf_candidat": categorie_naf_candidat,
                            "siret_candidat": siret_candidat,
                            "nom_candidat": nom_candidat,
                            "latitude_candidat": latitude,
                            "longitude_candidat": longitude,
                            "nombre_etablisseme"
                            "nts_ouverts": nombre_etablissements_ouverts,
                            "siege_flag": False,
                            "search_by_siret_candidat": search_by_siret_candidat,
                        }
                    )

                return res
            else:
                return []

        else:
            return []

    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue lors de la requête: {e}")
        return []


@sleep_and_retry
@limits(calls=40, period=1)
def get_lat_lon_from_address(address):
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address, "limit": 1}
    if address is None:
        return None, None
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "features" in data and data["features"]:
            coords = data["features"][0]["geometry"]["coordinates"]
            return coords[1], coords[0]

    return None, None

import requests
from ratelimit import limits


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


@limits(calls=7, period=1)
def call_annuaire_entreprises(query):
    params = {"q": query, "page": 1, "per_page": 1}
    base_url = "https://recherche-entreprises.api.gouv.fr"
    endpoint = "/search"
    try:
        response = requests.get(url=f"{base_url}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            if "results" in data and data["results"]:
                data = data["results"][0]
                (
                    adresse,
                    etat_admin,
                    siret,
                    categorie_naf,
                    etat_admin_siege,
                    categorie_naf_siege,
                    nombre_etablissements_ouverts,
                ) = (None, None, None, None, None, None, None)
                nombre_etablissements_ouverts = data.get(
                    "nombre_etablissements_ouverts"
                )
                if data.get("nombre_etablissements_ouverts") >= 1:
                    siege = data.get("siege", {})
                    adresse = siege.get("adresse")
                    etat_admin_siege = siege.get("etat_administratif")
                    siret = siege.get("siret")
                    categorie_naf_siege = siege.get("activite_principale")
                matching_etablissements = data.get("matching_etablissements", [])
                if matching_etablissements:
                    premier_etablissement = matching_etablissements[0]
                    etat_admin = premier_etablissement.get("etat_administratif")
                    categorie_naf = premier_etablissement.get("activite_principale")

                return {
                    "adresse": adresse,
                    "etat_admin": etat_admin,
                    "etat_admin_siege": etat_admin_siege,
                    "siret_siege": siret,
                    "categorie_naf_siege": categorie_naf_siege,
                    "categorie_naf": categorie_naf,
                    "nombre_etablissements_ouverts": nombre_etablissements_ouverts,
                }
            else:
                # Si 'results' est vide ou n'existe pas, retourner un dictionnaire vide
                return {}

        else:
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue lors de la requête: {e}")
        return {"error": "Une erreur de requête est survenue"}


@limits(calls=50, period=1)
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

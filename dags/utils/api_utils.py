import requests
from ratelimiter import RateLimiter


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


@RateLimiter(max_calls=7, period=1)
def call_annuaire_entreprises(query):
    params = {"q": query, "page": 1, "per_page": 1}
    base_url = "https://recherche-entreprises.api.gouv.fr"
    endpoint = "/search"
    try:
        response = requests.get(url=f"{base_url}{endpoint}", params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Une erreur est survenue lors de la requête: {e}")
        return ["Une erreur de requête est survenue"]

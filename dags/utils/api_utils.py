import requests


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

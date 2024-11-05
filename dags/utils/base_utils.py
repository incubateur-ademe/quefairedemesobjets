import csv
import io
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from fuzzywuzzy import fuzz
from shapely import wkb
from shapely.geometry import Point
from utils import api_utils


def get_address(row, col="adresse_format_ban"):
    if pd.isnull(row[col]):
        return pd.Series([None, None, None])

    res = get_address_from_ban(str(row[col]))
    match_percentage = res.get("match_percentage", 0)
    threshold = 80
    if match_percentage >= threshold:
        address = res.get("address")
        postal_code = res.get("postal_code")
        city = res.get("city")

        if not address or not postal_code or not city:
            address, postal_code, city = extract_details(row, col)
    else:
        address, postal_code, city = extract_details(row, col)

    return pd.Series([address, postal_code, city])


def get_mapping_config(mapping_key: str = "sous_categories"):
    config_path = Path(__file__).parent.parent / "config" / "db_mapping.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    return config[mapping_key]


def get_address_from_ban(address):
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address, "limit": 1}
    if address is None:
        return {}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "features" in data and data["features"]:
            properties = data["features"][0]["properties"]
            label = properties.get("label")
            query = data["query"]
            address = properties.get("name")
            postal_code = properties.get("postcode")
            city = properties.get("city")
            match_percentage = fuzz.ratio(query.lower(), label.lower())
            coords = (
                data["features"][0].get("geometry", {}).get("coordinates", [None, None])
            )
            return {
                "latitude": coords[1],
                "longitude": coords[0],
                "query": query,
                "label": label,
                "address": address,
                "postal_code": postal_code,
                "city": city,
                "match_percentage": match_percentage,
            }
    return {}


def extract_details(row, col="adresse_format_ban"):
    # Pattern pour capturer les codes postaux et les noms de ville optionnels
    pattern = re.compile(r"(.*?)\s+(\d{4,5})\s+(.*)")

    if pd.isnull(row[col]):
        return pd.Series([None, None, None])

    match = pattern.search(str(row[col]))
    if match:
        address = match.group(1).strip()
        postal_code = match.group(2).strip()
        city = match.group(3).strip() if match.group(3) else None

        # Ajouter un zéro si le code postal a quatre chiffres
        if len(postal_code) == 4:
            postal_code += "0"
        return pd.Series([address, postal_code, city])
    else:
        return pd.Series([None, None, None])


def transform_location(longitude, latitude):
    return wkb.dumps(Point(longitude, latitude)).hex()


def send_batch_to_api(batch):
    """
    Send a batch of CSV lines to the geocoding API and return the response.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["identifiant_unique", "adresse", "adresse_complement", "code_postal", "ville"]
    )
    for element in batch:
        row = element.values()
        writer.writerow(row)
    output.seek(0)
    response = requests.post(
        "https://api-adresse.data.gouv.fr/search/csv/",
        files={"data": output.getvalue()},
        data={
            "columns": ["adresse", "ville", "adresse_complement"],
            "postcode": "code_postal",
        },
    )
    reader = csv.DictReader(io.StringIO(response.text))
    return [row for row in reader]


def process_search_api_response(element):
    """
    Process each element returned from the search API and update address information.

    Args:
        element (dict): A dictionary containing data from the search API response.

    Returns:
        tuple: The updated element and a boolean indicating if the status is not 'ok'.
    """
    is_non_ok = element["result_status"] != "ok"
    if not is_non_ok:
        # Update address and city from the response
        element["adresse"] = element["result_name"]
        element["ville"] = element["result_city"]
        element["code_postal"] = element["result_postcode"]
        element["adresse_complement"] = element["adresse_complement"]
        element["st_x"] = element["longitude"]
        element["st_y"] = element["latitude"]
    return element, is_non_ok


def apply_normalization(df, normalization_map):
    """
    Apply normalization functions to the specified columns of a DataFrame.
    """
    df = normalize_address(df)
    for column, normalize_func in normalization_map.items():
        if column in df.columns:
            df[column] = df[column].apply(normalize_func)
        else:
            print(f"Column {column} not found in DataFrame.")
    return df


def normalize_address(df, batch_size=10000):
    """
    Normalize the addresses in the DataFrame using the Ban API.
    """
    # Determine the number of batches
    num_batches = len(df) // batch_size + (len(df) % batch_size > 0)

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = start_idx + batch_size

        # Extract relevant columns for address normalization
        address_data = df.loc[
            start_idx:end_idx,
            [
                "identifiant_unique",
                "adresse",
                "adresse_complement",
                "code_postal",
                "ville",
            ],
        ]
        address_list = address_data.to_dict(orient="records")

        # Send data to Ban API and receive normalized data
        normalized_data = send_batch_to_api(address_list)

        # Process each element from the normalized data
        for j, element in enumerate(normalized_data):
            updated_element, is_non_ok = process_search_api_response(element)
            if is_non_ok:
                pass

            df.loc[start_idx + j, "adresse"] = updated_element["adresse"]
            df.loc[start_idx + j, "ville"] = updated_element["ville"]
            df.loc[start_idx + j, "code_postal"] = updated_element["code_postal"]

    return df


def formatted_string(string: str) -> str:
    result = string.title().strip().replace("  ", " ").replace("/", "")

    if result.upper().startswith("SA "):
        result = "SA " + result[3:]
    if result.upper().startswith("SA."):
        result = "SA." + result[3:]
    if result.upper().endswith(" SA"):
        result = result[:-3] + " SA"

    if result.upper().startswith("SAS "):
        result = "SAS " + result[4:]
    if result.upper().startswith("SAS."):
        result = "SAS." + result[4:]
    if result.upper().endswith(" SAS"):
        result = result[:-4] + " SAS"

    for word in result.split(" "):
        if len(word) >= 3 and re.match("^[^aeiouAEIOU]+$", word):
            result = result.replace(word, word.upper())

    if result.upper().startswith("SARL "):
        result = "SARL " + result[5:]
    if result.upper().endswith(" SARL"):
        result = result[:-5] + " SARL"
    result = result.replace(" Sarl ", " SARL ")

    if result.upper().startswith("ETS "):
        result = "Éts " + result[4:]
    if result.upper().endswith(" ETS"):
        result = result[:-4] + " Éts"
    result = result.replace(" Ets ", " Éts ")

    result = result.replace("Boîte À Lire", "Boîte à lire")
    result = result.replace("D Or", "D'Or")

    return result


def save_to_database(df, table_name, engine):
    df.to_sql(table_name, engine, if_exists="replace", index=False)


def get_difference_counts(df_differences):
    return df_differences.count()


def normalize_phone_number(phone_number):
    if pd.isnull(phone_number):
        return None
    # Remove all non-numeric characters
    cleaned_phone = re.sub(r"\D", "", phone_number)
    # You can add more formatting logic here if needed
    return cleaned_phone


def normalize_nom(value):
    if pd.isnull(value):
        return None
    return formatted_string(value)


def normalize_email(email):
    if pd.isnull(email):
        return None
    # Convert the email to lowercase
    return email.lower()


def normalize_url(url):
    if pd.isnull(url):
        return None
    try:
        parsed_url = urlparse(url)
        # Extract the network location part (domain)
        domain = parsed_url.netloc
        # Remove 'www.' if it's part of the domain
        domain = domain.replace("www.", "")
        return domain
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return None


def find_differences(df_act, df_rev_act, columns_to_exclude, normalization_map):
    # Join the DataFrames on 'identifiant_unique'
    df_merged = pd.merge(
        df_act, df_rev_act, on="identifiant_unique", suffixes=("_act", "_rev_act")
    )
    df_merged["code_postal_act"] = pd.to_numeric(
        df_merged["code_postal_act"], errors="coerce"
    ).astype(pd.Int64Dtype())
    df_merged["code_postal_rev_act"] = pd.to_numeric(
        df_merged["code_postal_rev_act"], errors="coerce"
    ).astype(pd.Int64Dtype())

    suffixes = ["_act", "_rev_act"]

    # Apply the functions to the respective columns
    for base_col, func in normalization_map.items():
        for suffix in suffixes:
            col = base_col + suffix
            if col in df_merged.columns:
                df_merged[col] = df_merged[col].apply(func)
            else:
                print(f"Column {col} not found in DataFrame.")
    # Initialize a DataFrame to hold the differences
    df_differences = pd.DataFrame()
    df_differences["identifiant_unique"] = df_merged["identifiant_unique"]

    columns_to_exclude = columns_to_exclude

    for col in df_act.columns:
        if col not in columns_to_exclude:
            # Define the column names for act and rev_act
            col_act = col + "_act"
            col_rev_act = col + "_rev_act"

            # Create masks for non-empty and differing values
            mask_non_empty = (
                df_merged[col_rev_act].notnull()
                & (df_merged[col_act] != "")
                & (df_merged[col_rev_act] != "")
            )
            mask_different = df_merged[col_act] != df_merged[col_rev_act]

            # Apply masks and add to df_differences
            df_differences[col] = df_merged[col_rev_act].where(
                mask_non_empty & mask_different, None
            )

    # Remove rows where all elements are None (no differences found)
    df_differences = df_differences.dropna(
        how="all",
        subset=[col for col in df_differences.columns if col != "identifiant_unique"],
    )
    return df_differences


def check_siret_using_annuaire_entreprise(
    row, adresse_query_flag=False, query_col="siret", naf_col=None
):
    res = api_utils.call_annuaire_entreprises(
        row[query_col], adresse_query_flag=adresse_query_flag, naf=row.get(naf_col)
    )
    return res


def get_location(lon: float, lat: float) -> dict:
    try:

        if math.isnan(float(lon)) or math.isnan(float(lat)):
            return None

        location = transform_location(longitude=lon, latitude=lat)

        return {"latitude": lat, "longitude": lon, "location": location}

    except (ValueError, TypeError, Exception):
        return None

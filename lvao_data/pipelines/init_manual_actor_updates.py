import pandas as pd
import re
from sqlalchemy import create_engine
from urllib.parse import urlparse


class LVAOActorsDAO:
    def __init__(self, user, password, host, port, db_name):
        self.connection_string = (
            f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        )
        self.engine = create_engine(self.connection_string)

    def load_table(self, table_name):
        return pd.read_sql_table(table_name, self.engine)

    def apply_normalization(self, df, normalization_map):
        """
        Apply normalization functions to the specified columns of a DataFrame.
        """
        for column, normalize_func in normalization_map.items():
            if column in df.columns:
                df[column] = df[column].apply(normalize_func)
            else:
                print(f"Column {column} not found in DataFrame.")
        return df

    def find_differences(
        self, df_act, df_rev_act, columns_to_exclude, normalization_map
    ):
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
                    df_merged[col_act].notnull()
                    & df_merged[col_rev_act].notnull()
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
            subset=[
                col for col in df_differences.columns if col != "identifiant_unique"
            ],
        )
        return df_differences

    def formatted_string(self, string: str) -> str:
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

    def save_to_database(self, df, table_name):
        df.to_sql(table_name, self.engine, if_exists="replace", index=False)

    def get_difference_counts(self, df_differences):
        return df_differences.count()

    def normalize_phone_number(self, phone_number):
        if pd.isnull(phone_number):
            return None
        # Remove all non-numeric characters
        cleaned_phone = re.sub(r"\D", "", phone_number)
        # You can add more formatting logic here if needed
        return cleaned_phone

    def normalize_nom(self, value):
        if pd.isnull(value):
            return None
        return self.formatted_string(value)

    def normalize_email(self, email):
        if pd.isnull(email):
            return None
        # Convert the email to lowercase
        return email.lower()

    def normalize_url(self, url):
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


if __name__ == "__main__":
    # Usage
    user = "qfdmo"
    password = "qfdmo"
    host = "localhost"
    port = "6543"
    db_name = "qfdmo"

    handler = LVAOActorsDAO(user, password, host, port, db_name)

    df_act = handler.load_table("qfdmo_acteur")
    df_rev_act = handler.load_table("qfdmo_revisionacteur")

    columns_to_exclude = ["identifiant_unique", "statut", "cree_le", "modifie_le"]
    normalization_map = {
        "nom": handler.normalize_nom,
        "nom_commercial": handler.normalize_nom,
        "ville": handler.normalize_nom,
        "url": handler.normalize_url,
        "adresse": handler.normalize_nom,
        "adresse_complement": handler.normalize_nom,
        "email": handler.normalize_email,
        "telephone": handler.normalize_phone_number,
    }
    df_differences = handler.find_differences(
        df_act, df_rev_act, columns_to_exclude, normalization_map
    )

    df_act_cleaned = handler.apply_normalization(df_act, normalization_map)

    print(df_differences.count())

    handler.save_to_database(df_differences, "lvao_manual_actors_updates")
    handler.save_to_database(df_act_cleaned, "lvao_actors_processed")

#!/bin/python

"""Script to read a CSV, infer its schema, and test it in a PostgreSQL database."""
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rich import print
from rich.progress import track
from rich.prompt import Confirm, Prompt
from rich.traceback import install
from sqlalchemy import create_engine

install()

DATABASE_URL = os.environ["DATABASE_URL"]
print(f"{DATABASE_URL=}")
ENGINE = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")


def df_infer_schema_fast(csv_path: Path, delimiter) -> dict[str, str]:
    print("\nCSV reading 1st line: started 🟡")
    with csv_path.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        fields = next(reader)  # Read the first line
    print("CSV reading 1st line: completed 🟢")
    schema = {k: "VARCHAR(255)" for k in fields}
    print(f"{schema=}")
    return schema


def df_infer_schema_slow(csv_path: Path) -> dict[str, str]:
    """Infer table schema from a dataframe, in slow mode (
    i.e. by scanning all the data)."""
    print("\nCSV loading: started 🟡")
    df = pd.read_csv(csv_path, dtype="object")
    df = df.replace({np.nan: None})
    print("CSV loading: completed 🟢")
    print("\nInfer column lengths: started 🟡")
    lengths: dict[str, int] = {}
    for col in df.columns:
        max_len = df[col].dropna().astype(str).str.len().max()
        lengths[col] = (
            int(max_len) if pd.notnull(max_len) else 1
        )  # default to 1 if empty
    print("Infer column lengths: completed 🟢")

    schema = {k: f"VARCHAR({v})" for k, v in lengths.items()}
    print(f"{schema=}")
    return schema


def db_table_schema_create(table_name: str, schema: dict[str, str]) -> None:
    """Generate a PostgreSQL CREATE TABLE statement."""

    # Prepare SQL
    columns = []
    for col, datatype in schema.items():
        safe_col = col.replace('"', '""')
        columns.append(f'"{safe_col}" {datatype}')
    sql = ",\n  ".join(columns)
    sql = f"""DROP TABLE IF EXISTS {table_name};
    CREATE TABLE "{table_name}" (\n  {sql}\n);"""
    print(sql)

    # Run SQL if user wants to
    if Confirm.ask("\nCréer le schema?"):
        print("Création du schema")
        with ENGINE.connect() as conn:  # type: ignore
            conn.execute(sql)


def db_table_load_csv(csv_path: Path, delimiter: str, table_name: str) -> None:
    """Loading CSV into database. We intentionally use the STDIN method
    because when we load CSVs via our Airflow DAGs that's how we proceed
    (we stream download -> unpack -> load into DB that way)."""
    if not Confirm.ask("\nCharger le CSV?"):
        return

    # Preparing command
    cmd_copy = f"COPY {table_name} FROM stdin WITH (FORMAT csv, HEADER true, DELIMITER '{delimiter}');"
    cmd_psql = f'psql {DATABASE_URL} -c "{cmd_copy}"'
    cmd_final = f"cat '{csv_path}' | {cmd_psql}"
    print(f"{cmd_final=}")

    process = subprocess.Popen(
        cmd_final,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise SystemError(f"Error occurred: {stderr.decode()}")


def db_table_inspect(table_name: str, schema: dict[str, str]) -> None:
    print("\nInspecting loaded table:")
    cols = [k for k, v in schema.items() if v.startswith("VARCHAR")]
    results = []
    for col in track(cols):
        sql = f"""SELECT
                    '{col}' AS column,
                    MIN(LENGTH("{col}")) AS min_length,
                    MAX(LENGTH("{col}")) AS max_length
                FROM {table_name};"""
        df_result = pd.read_sql(sql, ENGINE)
        print(f"\n{col=}")
        print(df_result.drop(columns=["column"]))
        results += df_result.to_dict(orient="records")
    schema_loaded = {x["column"]: f"VARCHAR({x['max_length']})" for x in results}
    db_table_schema_create(f"{table_name}", schema_loaded)


def csv_schema_to_db(
    csv_path: Path,
    delimiter: str,
    table_name: str,
) -> None:
    """Load a CSV file into a PostgreSQL table."""
    # Load CSV

    schema = df_infer_schema_fast(csv_path, delimiter)
    db_table_schema_create(table_name, schema)
    db_table_load_csv(csv_path, delimiter, table_name)
    db_table_inspect(table_name, schema)


def main():

    # CSV path
    print("\nCSV path:")
    csv_path = Path(os.path.abspath(sys.argv[1]))
    print(f"{csv_path=}")
    assert csv_path.exists(), f"File not found: {csv_path}"

    delimiter = Prompt.ask("Délimiteur CSV:", default=",")
    print(f"{delimiter=}")

    # Database connection
    print("\nDatabase connection:")
    print(f"{DATABASE_URL=}")

    # Table name
    print("\nTable name:")
    table_name = f"test_schema_{re.sub(r"[ -]","_",csv_path.stem.lower())}"
    table_name = Prompt.ask("Enter table name:", default=table_name)
    print(f"{table_name=}")

    # Load CSV into DB
    csv_schema_to_db(csv_path, delimiter, table_name)


if __name__ == "__main__":
    main()

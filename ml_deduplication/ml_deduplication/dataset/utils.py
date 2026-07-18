from pathlib import Path


def get_sql_files_folder_path() -> Path:
    sql_query_folder = Path(__file__).parent / "sql"

    return sql_query_folder

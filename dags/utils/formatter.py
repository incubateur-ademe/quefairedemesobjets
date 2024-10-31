import unidecode


def format_libelle_to_code(input_str: str) -> str:
    return unidecode.unidecode(input_str).strip().lower()

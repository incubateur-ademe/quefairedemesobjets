from enrich.config.columns import SUGGEST_PREFIX


def dbt_model_row_to_suggest_data(row: dict) -> dict:
    """Construct the pydantic model_params.data dict from a
    dbt model's row based on fields prefixed with SUGGEST_PREFIX"""
    pre = SUGGEST_PREFIX
    keys_ok = [k for k in row.keys() if k.startswith(f"{pre}_")]
    keys_ok.remove(f"{pre}_cohort")

    # Validation
    keys_fail = [
        k
        for k in row.keys()
        if pre in k and k not in keys_ok and not k.startswith(f"{pre}_")
    ]
    if keys_fail:
        msg = f"Colonnes invalides avec {pre} mais sans {pre}_: {keys_fail}"
        raise KeyError(msg)

    # Construct the data dict
    return {k.replace(pre + "_", ""): row[k] for k in keys_ok}

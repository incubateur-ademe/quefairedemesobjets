import polars as pl

OPTIMIZED_SCHEMA = {
    "identifiant_unique": pl.String,
    "source_id": pl.Int16,
    "acteur_type_id": pl.Int8,
    "parent_id": pl.String,
    "cluster_id": pl.Categorical,
    "cluster_id_split": pl.Categorical,
    "example_type": pl.Categorical,
    "naf_principal": pl.Categorical,
    "public_accueilli": pl.Categorical,
    "reprise": pl.Categorical,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "code_commune_insee": pl.Categorical,
    "split": pl.Categorical,
}

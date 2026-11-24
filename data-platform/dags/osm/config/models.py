"""Configuration model for OSM Extract and Load DAG"""

from pydantic import AnyUrl, BaseModel, field_validator


class OSMExtractLoadConfig(BaseModel):
    dry_run: bool

    osm_dataset_url: AnyUrl

    # ---------------------------------------
    # Validation
    # ---------------------------------------
    # Champs isolés
    @field_validator("dry_run", mode="before")
    def check_dry_run(cls, v):
        if v is None:
            raise ValueError("dry_run à fournir")
        return v

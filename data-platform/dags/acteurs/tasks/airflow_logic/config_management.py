from pydantic import BaseModel


class ExportOpendataConfig(BaseModel):
    bucket_name: str
    remote_dir: str
    s3_connection_id: str
    opendata_table: str

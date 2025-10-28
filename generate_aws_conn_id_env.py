import os

from airflow.models.connection import Connection

conn = Connection(
    conn_id="aws_default",
    conn_type="aws",
    login="XXX",  # pragma: allowlist secret
    password="YY",  # pragma: allowlist secret
    extra={
        "aws_access_key_id": "XXX",  # pragma: allowlist secret
        "aws_secret_access_key": "YY",  # pragma: allowlist secret
        "host": "s3.fr-par.scw.cloud",
        "region": "fr-par",
        "endpoint_url": "https://s3.fr-par.scw.cloud",
        "port": 443,
        "use_ssl": True,
        "verify": False,
    },
)

# Generate Environment Variable Name and Connection URI
env_key = f"AIRFLOW_CONN_{conn.conn_id.upper()}"
conn_uri = conn.get_uri()
print(f"{env_key}={conn_uri}")

os.environ[env_key] = conn_uri
print(conn.test_connection())  # Validate connection credentials.

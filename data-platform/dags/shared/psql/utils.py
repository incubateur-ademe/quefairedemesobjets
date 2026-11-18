import os
from urllib.parse import parse_qsl, unquote, urlparse

# libpq URI query keys -> environment variables. Anything else is rejected so a
# security-relevant option (sslmode, certificates, …) cannot be dropped silently.
_DSN_QUERY_TO_ENV = {
    "host": "PGHOST",
    "hostaddr": "PGHOSTADDR",
    "port": "PGPORT",
    "dbname": "PGDATABASE",
    "user": "PGUSER",
    "password": "PGPASSWORD",  # pragma: allowlist secret
    "sslmode": "PGSSLMODE",
    "requiressl": "PGREQUIRESSL",
    "sslcompression": "PGSSLCOMPRESSION",
    "sslcert": "PGSSLCERT",
    "sslkey": "PGSSLKEY",
    "sslrootcert": "PGSSLROOTCERT",
    "sslcrl": "PGSSLCRL",
    "sslcrldir": "PGSSLCRLDIR",
    "sslsni": "PGSSLSNI",
    "requirepeer": "PGREQUIREPEER",
    "ssl_min_protocol_version": "PGSSLMINPROTOCOLVERSION",
    "ssl_max_protocol_version": "PGSSLMAXPROTOCOLVERSION",
    "gssencmode": "PGGSSENCMODE",
    "krbsrvname": "PGKRBSRVNAME",
    "gsslib": "PGGSSLIB",
    "connect_timeout": "PGCONNECT_TIMEOUT",
    "client_encoding": "PGCLIENTENCODING",
    "target_session_attrs": "PGTARGETSESSIONATTRS",
    "channel_binding": "PGCHANNELBINDING",
    "options": "PGOPTIONS",
    "application_name": "PGAPPNAME",
    "passfile": "PGPASSFILE",
    "service": "PGSERVICE",
}


def psql_env_from_dsn(dsn: str) -> dict[str, str]:
    """Build a psql environment from a connection URI.

    Credentials stay in environment variables. ``CalledProcessError``
    stringifies argv, which Airflow writes to the task log.
    """
    parsed = urlparse(dsn)
    env = os.environ.copy()
    if parsed.hostname:
        env["PGHOST"] = parsed.hostname
    if parsed.port:
        env["PGPORT"] = str(parsed.port)
    if parsed.username:
        env["PGUSER"] = unquote(parsed.username)
    database = unquote(parsed.path.lstrip("/"))
    if database:
        env["PGDATABASE"] = database
    if parsed.password is not None:
        env["PGPASSWORD"] = unquote(parsed.password)

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        env_name = _DSN_QUERY_TO_ENV.get(key)
        if env_name is None:
            raise ValueError(f"Unsupported PostgreSQL DSN parameter: {key}")
        env[env_name] = value
    return env

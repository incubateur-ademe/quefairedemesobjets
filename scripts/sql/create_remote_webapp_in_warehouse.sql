-- Set up postgres_fdw foreign access from warehouse DB to webapp DB.
-- Mirrors `create_schema_webapp_public_in_warehouse_db()` in webapp/core/utils.py.
-- Required psql variables (-v key=value): webapp_host, webapp_port,
--   webapp_dbname, webapp_user, webapp_password.

CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SERVER IF EXISTS webapp_server CASCADE;

CREATE SERVER webapp_server FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (
    host :'webapp_host',
    port :'webapp_port',
    dbname :'webapp_dbname'
  );

CREATE USER MAPPING FOR CURRENT_USER SERVER webapp_server
  OPTIONS (
    user :'webapp_user',
    password :'webapp_password'
  );

CREATE SCHEMA IF NOT EXISTS webapp_public;

IMPORT FOREIGN SCHEMA public FROM SERVER webapp_server
INTO webapp_public;

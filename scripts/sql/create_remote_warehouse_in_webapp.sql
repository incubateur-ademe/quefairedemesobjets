-- Set up postgres_fdw foreign access from webapp DB to warehouse DB.
-- Mirrors `create_schema_warehouse_public_in_webapp_db()` in webapp/core/utils.py.
-- Required psql variables (-v key=value): warehouse_host, warehouse_port,
--   warehouse_dbname, warehouse_user, warehouse_password.

CREATE EXTENSION IF NOT EXISTS postgres_fdw;

DROP SERVER IF EXISTS warehouse_server CASCADE;

CREATE SERVER warehouse_server FOREIGN DATA WRAPPER postgres_fdw
  OPTIONS (
    host :'warehouse_host',
    port :'warehouse_port',
    dbname :'warehouse_dbname'
  );

CREATE USER MAPPING FOR CURRENT_USER SERVER warehouse_server
  OPTIONS (
    user :'warehouse_user',
    password :'warehouse_password'
  );

CREATE SCHEMA IF NOT EXISTS warehouse_public;

IMPORT FOREIGN SCHEMA public FROM SERVER warehouse_server
INTO warehouse_public;

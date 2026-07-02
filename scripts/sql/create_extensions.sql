-- Create extensions if they don't exist
-- This is needed because restoration of the DB remove those extensions
-- And thay are not restored by the pg_restore command

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Note: the wagtail_french text search configuration is created by the
-- dedicated scripts/sql/create_wagtail_french_config.sql, run right after
-- this file by every caller.

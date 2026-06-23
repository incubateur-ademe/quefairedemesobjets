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

-- Keep in sync with scripts/sql/create_wagtail_french_config.sql, which the
-- qfdmd 0045 migration reads. Inlined here (not \ir-included) because this
-- file is also executed via psycopg by create_webapp_sample_db.py, and
-- psycopg does not understand psql meta-commands like \ir.
CREATE EXTENSION IF NOT EXISTS unaccent;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_ts_config WHERE cfgname = 'wagtail_french'
  ) THEN
    CREATE TEXT SEARCH CONFIGURATION wagtail_french (COPY = french);
    ALTER TEXT SEARCH CONFIGURATION wagtail_french
      ALTER MAPPING FOR hword, hword_part, word
      WITH unaccent, french_stem;
  END IF;
END
$$;

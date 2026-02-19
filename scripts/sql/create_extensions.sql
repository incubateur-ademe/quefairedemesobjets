-- Create extensions if they don't exist
-- This is needed because restoration of the DB remove those extensions
-- And thay are not restored by the pg_restore command

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TEXT SEARCH CONFIGURATION wagtail_french (COPY = french);
ALTER TEXT SEARCH CONFIGURATION wagtail_french
  ALTER MAPPING FOR hword, hword_part, word
  WITH unaccent, french_stem;

-- Creates the wagtail_french text search configuration used by the Postgres
-- search backend. Run as a dedicated step right after create_extensions.sql by
-- every caller (qfdmd migration 0045 via Django, create_webapp_sample_db.py via
-- psycopg, and the Makefile load-*-dump / create-extensions targets via psql),
-- so there is exactly one definition.
--
-- Postgres has no CREATE ... IF NOT EXISTS for text search configurations, so
-- the creation is guarded manually and is therefore safe to run repeatedly.
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

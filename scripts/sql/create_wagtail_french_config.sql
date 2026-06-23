-- Creates the wagtail_french text search configuration used by the Postgres
-- search backend. Shared between qfdmd migration 0045 (runs via Django on the
-- test/fresh DB) and create_extensions.sql (runs via psql on local restores),
-- so the two never drift.
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

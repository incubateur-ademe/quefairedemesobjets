-- Readonly access for a Metabase user, including objects created later.
-- Scaleway permission=readonly only GRANTs on objects that already exist.
-- Required psql variables (-v key=value): owner_user, metabase_user
--
-- owner_user is the role that creates tables (Django / dbt / clone / FDW).
-- Default privileges must be set FOR that role, not for the Metabase user.

-- Existing non-system schemas (public, webapp_public, …)
SELECT format('GRANT USAGE ON SCHEMA %I TO %I', n.nspname, :'metabase_user')
FROM pg_namespace n
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND n.nspname NOT LIKE 'pg\_%'
\gexec

SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I', n.nspname, :'metabase_user')
FROM pg_namespace n
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND n.nspname NOT LIKE 'pg\_%'
\gexec

SELECT format('GRANT SELECT ON ALL SEQUENCES IN SCHEMA %I TO %I', n.nspname, :'metabase_user')
FROM pg_namespace n
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND n.nspname NOT LIKE 'pg\_%'
\gexec

-- Future objects created by the owner, in any schema
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_user"
  GRANT USAGE ON SCHEMAS TO :"metabase_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_user"
  GRANT SELECT ON TABLES TO :"metabase_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_user"
  GRANT SELECT ON SEQUENCES TO :"metabase_user";

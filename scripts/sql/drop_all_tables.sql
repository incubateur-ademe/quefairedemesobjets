-- Script to remove tables and views in the public schema

-- Disable all foreign key constraints
DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    -- Désactiver toutes les contraintes de clés étrangères
    FOR constraint_rec IN
        SELECT
            tc.table_name,
            tc.constraint_name
        FROM
            information_schema.table_constraints tc
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I CASCADE',
                      constraint_rec.table_name,
                      constraint_rec.constraint_name);
    END LOOP;
END $$;


-- Remove all views (excluding views from extensions)
DO $$
DECLARE
    view_rec RECORD;
BEGIN
    FOR view_rec IN
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        AND NOT EXISTS (
            SELECT 1 FROM pg_depend d
            JOIN pg_extension e ON d.refobjid = e.oid
            WHERE d.objid = (
                SELECT oid FROM pg_class
                WHERE relname = table_name AND relnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = 'public'
                )
            )
        )
    LOOP
        EXECUTE format('DROP VIEW IF EXISTS %I CASCADE', view_rec.table_name);
    END LOOP;
END $$;

-- Remove all tables (excluding tables from extensions)
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    FOR table_rec IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND NOT EXISTS (
            SELECT 1 FROM pg_depend d
            JOIN pg_extension e ON d.refobjid = e.oid
            WHERE d.objid = (
                SELECT oid FROM pg_class
                WHERE relname = table_name AND relnamespace = (
                    SELECT oid FROM pg_namespace WHERE nspname = 'public'
                )
            )
        )
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_rec.table_name);
    END LOOP;
END $$;


-- Display a confirmation message
SELECT 'All relations in the public schema have been removed successfully.' as message;

DROP VIEW IF EXISTS {{db_schema}}.{{view_name}} CASCADE;
CREATE VIEW {{db_schema}}.{{view_name}} AS (
    SELECT * FROM {{db_schema}}.{{table_name}}
)
SELECT
    CASE
        WHEN COUNT(*) >= 210000 THEN TRUE
        ELSE FALSE
    END AS is_valid,
    COUNT(*) as debug_value
FROM
    {{db_schema}}.{{table_name}};
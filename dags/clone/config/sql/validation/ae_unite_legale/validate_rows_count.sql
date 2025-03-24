SELECT
    CASE
        WHEN COUNT(*) >= 27766501 THEN TRUE
        ELSE FALSE
    END AS is_valid,
    COUNT(*) as debug_value
FROM
    {{table_name}};
SELECT
    CASE
        WHEN COUNT(*) >= 40067694 THEN TRUE
        ELSE FALSE
    END AS is_valid,
    COUNT(*) as debug_value
FROM
    {{table_name}};
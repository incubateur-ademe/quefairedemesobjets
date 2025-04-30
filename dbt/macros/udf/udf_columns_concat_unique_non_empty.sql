{% macro create_udf_columns_concat_unique_non_empty() %}
/*
    Concatenate strings from various columns while only retaining non-empty values
*/
CREATE OR REPLACE FUNCTION {{ target.schema }}.udf_columns_concat_unique_non_empty(VARIADIC input_columns TEXT[])
RETURNS TEXT AS $$
DECLARE
    unique_values TEXT;
BEGIN
    SELECT string_agg(DISTINCT val, ' ')
    INTO unique_values
    FROM unnest(input_columns) AS val
    WHERE val IS NOT NULL AND val != '';
    RETURN unique_values;
END;
$$ LANGUAGE plpgsql;
{% endmacro %}
{% macro create_udf_ae_string_cleanup() %}
/*
    Converts string values from Annuaire Entreprises
    to 1 consistent format, taking into account cases
    such as '[ND]' = Non disponible, with conversion
    to NULL for easier processing whenever we consider
    it to be empty.
*/
CREATE OR REPLACE FUNCTION {{ target.schema }}.udf_ae_string_cleanup(val TEXT)
RETURNS TEXT AS $$
BEGIN
    IF TRIM(val) = '' OR TRIM(val) = '[ND]' THEN
        RETURN NULL;
    ELSE
        RETURN TRIM(val);
    END IF;
END;
$$ LANGUAGE plpgsql STRICT;
{% endmacro %}
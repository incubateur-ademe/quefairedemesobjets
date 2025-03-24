{% macro create_udf_normalize_string_alpha_for_match() %}
/*
    Normalize strings for the purpose of matching.
    For instance for RGPD we want to identify acteurs which names
    are directors' names, but we cant just pull everything for processing
    in Python because as of 2025-03-17 there are 13M unite_legale rows
    with directors' names, hence normalization for a pre-filtering in SQL

    E.g. to test this function:
    SELECT udf_normalize_string_alpha_for_match(' Héllo-Wørld! Ça va? 123 ');
 */

DROP FUNCTION IF EXISTS {{ target.schema }}.udf_normalize_string_alpha_for_match(input_text TEXT);
CREATE FUNCTION {{ target.schema }}.udf_normalize_string_alpha_for_match(input_text TEXT) RETURNS TEXT AS $$
DECLARE
    normalized TEXT;
BEGIN
    normalized := unaccent(input_text);
    normalized := lower(normalized);
    normalized := regexp_replace(normalized, '[^a-z]', ' ', 'g');
    normalized := regexp_replace(normalized, '\s+', ' ', 'g');
    normalized := trim(normalized);

    RETURN normalized;
END;
$$ LANGUAGE plpgsql;
{% endmacro %}
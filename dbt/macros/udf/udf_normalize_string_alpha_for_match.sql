{% macro create_udf_normalize_string_alpha_for_match() %}
/*
    Function to normalize strings for the purpose of matching.
    For instance for RGPD we want to identify acteurs which names
    are directors' names, but we cant just pull everything for processing
    in Python because as of 2025-03-17 there are 13M unite_legale rows
    with directors' names, hence normalization for a pre-filtering in SQL

    E.g. to test this function:
    SELECT udf_normalize_string_alpha_for_match(' Héllo-Wørld! Ça va? 123 ');
 */
CREATE OR REPLACE FUNCTION udf_normalize_string_alpha_for_match(input_text TEXT) RETURNS TEXT AS $$
DECLARE
    normalized TEXT;
BEGIN
    -- Step 1: Transliterate using unaccent
    normalized := unaccent(input_text);

    -- Step 2: Convert to lowercase
    normalized := lower(normalized);

    -- Step 3: Replace non-alpha characters with space
    normalized := regexp_replace(normalized, '[^a-z]', ' ', 'g');

    -- Step 4: Replace multiple spaces with a single space
    normalized := regexp_replace(normalized, '\s+', ' ', 'g');

    -- Step 5: Trim leading and trailing spaces
    normalized := trim(normalized);

    RETURN normalized;
END;
$$ LANGUAGE plpgsql;
{% endmacro %}
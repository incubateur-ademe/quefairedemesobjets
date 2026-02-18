{% macro create_udf_normalize_string_alpha_for_match() %}
/*
    Normalize strings for the purpose of matching.
    For instance for RGPD we want to identify acteurs which names
    are directors' names, but we cant just pull everything for processing
    in Python because as of 2025-03-17 there are 13M unite_legale rows
    with directors' names, hence normalization for a pre-filtering in SQL

    E.g. to test this function:
    SELECT {{ target.schema }}.udf_normalize_string_for_match(' Héllo-Wørld! Ça va? 123 ');
 */
CREATE OR REPLACE FUNCTION {{ target.schema }}.udf_normalize_string_for_match(input_text TEXT, remove_words_smaller_size INTEGER DEFAULT 2) RETURNS TEXT AS $$
DECLARE
    normalized TEXT;
    words TEXT[];
BEGIN
    -- Step 1: Normalize the string
    normalized := unaccent(input_text);
    normalized := lower(normalized);
    normalized := regexp_replace(normalized, '[^a-z]', ' ', 'g');
    normalized := regexp_replace(normalized, '\s+', ' ', 'g');
    normalized := trim(normalized);

    -- Step 2: Split into words, sort alphabetically, and rejoin
    words := string_to_array(normalized, ' ');
    SELECT string_agg(word, ' ') INTO normalized
    FROM (
        SELECT unnest(words) AS word
        ORDER BY word
    ) AS words_sorted
    WHERE length(word) >= remove_words_smaller_size;

    RETURN normalized;
END;
$$ LANGUAGE plpgsql;
{% endmacro %}
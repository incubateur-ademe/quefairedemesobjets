{% macro create_udf_columns_words_in_common_count() %}
/*
    Count number of words in common between 2 columns
*/
CREATE OR REPLACE FUNCTION {{ target.schema }}.udf_columns_words_in_common_count(col1 text, col2 text)
RETURNS integer AS $$
DECLARE
    word text;
    count integer := 0;
BEGIN
    FOR word IN
        SELECT unnest(string_to_array(col1, ' '))
    LOOP
        -- TODO: accuracy could be improved with REGEXP boundaries to count whole words
        IF position(word IN col2) > 0 THEN
            count := count + 1;
        END IF;
    END LOOP;

    RETURN count;
END;
$$ LANGUAGE plpgsql;
{% endmacro %}
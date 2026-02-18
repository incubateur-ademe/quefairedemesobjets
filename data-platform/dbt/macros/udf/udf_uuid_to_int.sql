{% macro create_udf_uuid_to_int() %}
CREATE OR REPLACE FUNCTION {{ target.schema }}.uuid_to_int(uuid UUID)
RETURNS numeric AS $$
DECLARE
    uuid_str text;
    result numeric := 0;
    hex_digit text;
BEGIN
    -- Remove dashes from the UUID
    uuid_str := replace(uuid::text, '-', '');

    -- Convert hex to numeric by processing each digit
    -- uuid.int in Python treats the UUID as a 128-bit hexadecimal number
    FOR i IN 1..32 LOOP
        hex_digit := substr(uuid_str, i, 1);
        result := result * 16 + (
            CASE
                WHEN hex_digit BETWEEN '0' AND '9' THEN ascii(hex_digit) - ascii('0')
                WHEN hex_digit BETWEEN 'a' AND 'f' THEN ascii(hex_digit) - ascii('a') + 10
                WHEN hex_digit BETWEEN 'A' AND 'F' THEN ascii(hex_digit) - ascii('A') + 10
            END
        );
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

{% endmacro %}
{% macro create_uuid_to_int() %}

CREATE OR REPLACE FUNCTION {{ target.schema }}.uuid_to_int(uuid UUID)
RETURNS numeric AS $$
DECLARE
    uuid_str text;
    result numeric := 0;
    hex_digit text;
BEGIN
    -- Enlever les tirets de l'UUID
    uuid_str := replace(uuid::text, '-', '');

    -- Conversion hex vers numeric en traitant chaque digit
    -- uuid.int en Python traite l'UUID comme un nombre hexadécimal de 128 bits
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
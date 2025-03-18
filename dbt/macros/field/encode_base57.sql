{% macro create_encode_base57() %}

CREATE OR REPLACE FUNCTION {{ target.schema }}.encode_base57(uuid UUID)
RETURNS text AS $$
DECLARE
    alphabet text := '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'; -- pragma: allowlist secret
    result text := '';
    bytes bytea;
    val numeric;
    remainder int;
BEGIN
    -- Conversion UUID en bytea
    val := {{ target.schema }}.uuid_to_int(uuid);

    -- Conversion en base57
    WHILE val > 0 LOOP
        SELECT * FROM {{ target.schema }}.safe_divmod(val, 57) INTO val, remainder;
        result := substr(alphabet, remainder + 1, 1) || result;
    END LOOP;

    -- Padding
    WHILE length(result) < 22 LOOP
        result := substr(alphabet, 1, 1) || result;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

{% endmacro %}
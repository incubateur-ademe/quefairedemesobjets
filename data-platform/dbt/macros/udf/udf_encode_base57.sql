{% macro create_udf_encode_base57() %}

CREATE OR REPLACE FUNCTION {{ target.schema }}.encode_base57(uuid UUID)
RETURNS varchar(22) AS $$
DECLARE
    alphabet text := '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'; -- pragma: allowlist secret
    result text := '';
    val numeric;
    remainder int;
BEGIN
    -- Convert to int
    val := {{ target.schema }}.uuid_to_int(uuid);

    -- Convert to base57
    WHILE val > 0 LOOP
        SELECT * FROM {{ target.schema }}.safe_divmod(val, 57) INTO val, remainder;
        result := substr(alphabet, remainder + 1, 1) || result;
    END LOOP;

    -- Padding management
    WHILE length(result) < 22 LOOP
        result := substr(alphabet, 1, 1) || result;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

{% endmacro %}
{% macro create_safe_divmod() %}
CREATE OR REPLACE FUNCTION {{ target.schema }}.safe_divmod(n numeric, d numeric)
RETURNS TABLE(quotient numeric, remainder numeric) AS $$
DECLARE
    q numeric;
    r numeric;
BEGIN
    q := trunc(n/d);  -- Essayons trunc au lieu de floor
    r := n - (q * d); -- Calculons le reste par soustraction

    -- Ajustons si nécessaire pour garantir 0 ≤ r < d
    IF r < 0 THEN
        r := r + d;
        q := q - 1;
    END IF;

    RETURN QUERY SELECT q, r;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
{% endmacro %}
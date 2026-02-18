{% macro create_udf_safe_divmod() %}
CREATE OR REPLACE FUNCTION {{ target.schema }}.safe_divmod(n numeric, d numeric)
RETURNS TABLE(quotient numeric, remainder numeric) AS $$
DECLARE
    q numeric;
    r numeric;
BEGIN
    q := trunc(n/d);  -- Use trunc instead of floor
    r := n - (q * d); -- Calculate the remainder by subtraction

    -- Adjust if necessary to ensure 0 ≤ r < d
    IF r < 0 THEN
        r := r + d;
        q := q - 1;
    END IF;

    RETURN QUERY SELECT q, r;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;
{% endmacro %}
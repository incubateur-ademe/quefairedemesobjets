{% test at_least_one_not_empty(model, column_name) %}

    {# Cast to text: comparing float/jsonb to '' is invalid in Postgres. #}
    select 1
    where not exists (
        select 1
        from {{ model }}
        where {{ column_name }} is not null
          and {{ column_name }}::text not in ('', '{}', '[]')
    )

{% endtest %}

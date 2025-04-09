/* Constant used to flag a value as unavailable
and detect, test, exclude it more easily
vs. values such as "" or NULL which might raise
doubts about functionality of model */
{% macro value_unavailable() %}'🔴 VALEUR INDISPONIBLE'{% endmacro %}
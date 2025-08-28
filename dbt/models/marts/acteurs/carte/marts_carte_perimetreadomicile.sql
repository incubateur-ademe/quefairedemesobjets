-- depends_on: {{ ref('marts_carte_acteur') }}
-- depends_on: {{ ref('int_perimetreadomicile') }}

SELECT pad.*
FROM {{ ref('int_perimetreadomicile') }} AS pad
INNER JOIN {{ ref('marts_carte_acteur') }} AS a
    ON pad.acteur_id = a.identifiant_unique

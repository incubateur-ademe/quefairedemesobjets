SELECT displayed.*
FROM {{ ref('base_displayedacteur_labels') }} AS displayed
WHERE
    displayed.displayedacteur_id IN (
        SELECT sample.identifiant_unique
        FROM {{ ref('marts_sample_displayedacteur') }} AS sample
    )

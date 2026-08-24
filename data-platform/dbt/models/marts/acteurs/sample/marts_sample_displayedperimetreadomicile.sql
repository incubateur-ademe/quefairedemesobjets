SELECT displayed.*
FROM {{ ref('base_displayedperimetreadomicile') }} AS displayed
WHERE
    displayed.acteur_id IN (
        SELECT sample.identifiant_unique
        FROM {{ ref('marts_sample_displayedacteur') }} AS sample
    )

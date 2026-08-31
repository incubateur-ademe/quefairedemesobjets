SELECT displayed.*
FROM {{ ref('base_displayedpropositionservice_sous_categories') }} AS displayed
WHERE
    displayed.displayedpropositionservice_id IN (
        SELECT sample.id
        FROM {{ ref('marts_sample_displayedpropositionservice') }} AS sample
    )

SELECT displayedacteur.* FROM {{ ref('base_displayedacteur') }} AS displayedacteur
LEFT JOIN {{ ref('base_epci') }} AS epci ON displayedacteur.epci_id = epci.id
LEFT JOIN {{ ref('base_acteur_type') }} AS acteur_type ON displayedacteur.acteur_type_id = acteur_type.id
WHERE
    epci.code IN (
        '200043123', /* CC Auray Quiberon Terre Atlantique */
        '200065647' /* CA Pays de Montbéliard Agglomération */
    )
    OR acteur_type.code = 'acteur_digital' /* Include all digital acteurs */

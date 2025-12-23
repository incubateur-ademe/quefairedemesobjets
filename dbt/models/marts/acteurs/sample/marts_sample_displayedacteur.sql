SELECT displayedacteur.* FROM {{ source('qfdmo', 'qfdmo_displayedacteur') }} AS displayedacteur
LEFT JOIN {{ source('qfdmo','qfdmo_epci') }} AS epci ON displayedacteur.epci_id = epci.id
LEFT JOIN {{ source('qfdmo','qfdmo_acteurtype') }} AS acteur_type ON displayedacteur.acteur_type_id = acteur_type.id
WHERE
    epci.code IN (
        '200043123', /* CC Auray Quiberon Terre Atlantique */
        '200065647' /* CA Pays de Montbéliard Agglomération */
    )
    OR acteur_type.code = 'acteur_digital' /* Include all digital acteurs */

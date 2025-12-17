SELECT displayedacteur.* FROM {{ source('qfdmo', 'qfdmo_displayedacteur') }} AS displayedacteur
INNER JOIN {{ source('qfdmo','qfdmo_epci') }} AS epci ON displayedacteur.epci_id = epci.id
WHERE epci.code IN (
    '200043123', /* CC Auray Quiberon Terre Atlantique */
    '200065647' /* CA Pays de Montbéliard Agglomération */
    )
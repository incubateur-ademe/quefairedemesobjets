SELECT a.* FROM {{ source('qfdmo', 'qfdmo_displayedacteur') }} AS a
LEFT OUTER JOIN {{ source('qfdmo','qfdmo_epci') }} AS epci ON a.epci_id = epci.id
WHERE epci.code IN (
    '200043123', /* CC Auray Quiberon Terre Atlantique */
    '200065647' /* CA Pays de Montbéliard Agglomération */
    )
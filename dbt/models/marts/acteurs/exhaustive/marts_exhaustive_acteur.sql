select * from {{ ref('int_acteur') }}

/*
A faire après avoir modifié le process de publication des tables displayed
A lieu de renommer, on préfèrera faire une copie de carte -> displayed

Ajout des champs calculés:

est_parent                       | boolean                 |           |          |
 est_dans_displayedacteur         | boolean                 |           |          |
 est_dans_revisionacteur          | boolean                 |           |          |
 est_dans_acteur                  | boolean                 |           |          |
 location_lat                     | double precision        |           |          |
 location_long                    | double precision        |           |          |
 enfants_nombre                   | integer                 |           |          |
 enfants_liste                    | character varying[]     |           |          |
 source_code                      | character varying(255)  |           |          |
 acteur_type_code                 | character varying(255)

*/
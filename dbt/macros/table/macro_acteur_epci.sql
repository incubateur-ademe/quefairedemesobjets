{%- macro acteur_epci(ephemeral_filtered_acteur) -%}

WITH acteur_with_best_match AS (
  SELECT
    acteur.identifiant_unique,
    acteur.code_postal,
    UPPER(UNACCENT(acteur.ville)) AS upper_acteur_ville, -- pour débugger
    REPLACE(UPPER(UNACCENT(epci.nom_commune)), ' ARRONDISSEMENT', '') AS upper_epci_nom_commune, -- pour débugger
    laposte.code_commune_insee,
    epci.code_epci,
    epci.nom_epci,
    SIMILARITY(UPPER(UNACCENT(acteur.ville)), REPLACE(UPPER(UNACCENT(epci.nom_commune)), ' ARRONDISSEMENT', '')) as similarity_score,
    ROW_NUMBER() OVER (
      PARTITION BY acteur.identifiant_unique
      ORDER BY SIMILARITY(UPPER(UNACCENT(acteur.ville)), REPLACE(UPPER(UNACCENT(epci.nom_commune)), ' ARRONDISSEMENT', '')) DESC
    ) as rank
  FROM {{ ref(ephemeral_filtered_acteur) }} AS acteur
  LEFT JOIN {{ source('clone','clone_laposte_code_postal_in_use') }} AS laposte
    ON acteur.code_postal = laposte.code_postal
  LEFT JOIN {{ source('clone','clone_koumoul_epci_in_use') }} AS epci
    ON laposte.code_commune_insee = epci.code_commune
  WHERE SIMILARITY(UPPER(UNACCENT(acteur.ville)), REPLACE(UPPER(UNACCENT(epci.nom_commune)), ' ARRONDISSEMENT', '')) > 0.3
)

SELECT
  identifiant_unique,
  code_postal,
  upper_acteur_ville,
  upper_epci_nom_commune,
  code_commune_insee,
  code_epci,
  nom_epci,
  similarity_score
FROM acteur_with_best_match
WHERE rank = 1 AND code_postal IS NOT NULL


{%- endmacro -%}
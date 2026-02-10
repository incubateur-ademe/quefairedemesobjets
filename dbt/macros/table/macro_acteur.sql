{%- macro acteur(ephemeral_filtered_acteur, propositionservice, acteur_epci ) -%}

WITH enfants AS (
    select
        distinct(parent_id) as parent_id,
        jsonb_agg(identifiant_unique) as enfants
    from {{ ref(ephemeral_filtered_acteur) }}
    group by parent_id
),

parentacteur_lieuprestation AS (
    SELECT
    acteur.parent_id AS acteur_id,
    -- AGGREGATION, on prend le lieu de prestation dans l'ordre : SUR_PLACE_OU_A_DOMICILE, A_DOMICILE, SUR_PLACE
    CASE
      WHEN BOOL_OR(enfant.lieu_prestation = 'SUR_PLACE_OU_A_DOMICILE') THEN 'SUR_PLACE_OU_A_DOMICILE'
      WHEN BOOL_OR(enfant.lieu_prestation = 'A_DOMICILE') THEN 'A_DOMICILE'
      WHEN BOOL_OR(enfant.lieu_prestation = 'SUR_PLACE') THEN 'SUR_PLACE'
      ELSE NULL
    END AS lieu_prestation

    FROM {{ ref(ephemeral_filtered_acteur) }} AS acteur
    -- get only the acteur with propositionservice
    INNER JOIN {{ ref(propositionservice) }} AS ps
        ON acteur.identifiant_unique = ps.acteur_id
    -- get the children of the acteur
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS enfant
        ON enfant.parent_id = acteur.identifiant_unique
    WHERE enfant.lieu_prestation IS NOT NULL
    GROUP BY acteur.parent_id
)

SELECT DISTINCT efa.uuid,
    efa.identifiant_unique,
    efa.nom,
    {{ field_empty('efa.description') }} AS description,
    efa.acteur_type_id,
    {{ field_empty('efa.adresse') }} AS adresse,
    {{ field_empty('efa.adresse_complement') }} AS adresse_complement,
    {{ field_empty('efa.code_postal') }} AS code_postal,
    {{ field_empty('efa.ville') }} AS ville,
    {{ field_empty('efa.url') }} AS url,
    {{ field_empty('efa.email') }} AS email,
    efa.location,
    {{ field_empty('efa.telephone') }} AS telephone,
    {{ field_empty('efa.nom_commercial') }} AS nom_commercial,
    {{ field_empty('efa.nom_officiel') }} AS nom_officiel,
    {{ field_empty('efa.siren') }} AS siren,
    {{ field_empty('efa.siret') }} AS siret,
    efa.source_id,
    efa.identifiant_externe,
    efa.naf_principal,
    {{ field_empty('efa.commentaires') }} AS commentaires,
    {{ field_empty('efa.horaires_osm') }} AS horaires_osm,
    {{ field_empty('efa.horaires_description') }} AS horaires_description,
    efa.public_accueilli,
    efa.reprise,
    efa.exclusivite_de_reprisereparation,
    efa.uniquement_sur_rdv,
    {{ field_empty('efa.consignes_dacces') }} AS consignes_dacces,
    efa.action_principale_id,
    -- Résolution du lieu de prestation : si l' acteur est un parent et qu'il a des enfants, on prend le lieu de prestation compilé, sinon on prend le lieu de prestation de l'acteur
    CASE WHEN plp.acteur_id IS NOT NULL THEN plp.lieu_prestation ELSE efa.lieu_prestation END AS lieu_prestation,
    efa.modifie_le,
    efa.cree_le,
    efa.statut,
    efa.siret_is_closed,
    COALESCE(aepci.code_commune_insee, '') as code_commune_insee,
    epci.id as epci_id,
    e.enfants IS NOT NULL AS est_parent
FROM {{ ref(ephemeral_filtered_acteur) }} AS efa
LEFT JOIN enfants AS e
  ON efa.identifiant_unique = e.parent_id
INNER JOIN {{ ref(propositionservice) }} AS cps
    ON efa.identifiant_unique = cps.acteur_id
LEFT OUTER JOIN parentacteur_lieuprestation AS plp
    ON efa.identifiant_unique = plp.acteur_id
LEFT OUTER JOIN {{ ref(acteur_epci) }} AS aepci
    ON efa.identifiant_unique = aepci.identifiant_unique
LEFT OUTER JOIN {{ source('qfdmo','qfdmo_epci') }} AS epci
    ON aepci.code_epci = epci.code
-- filter to apply on resolved parent + children acteur
WHERE (efa.public_accueilli IS NULL OR UPPER(efa.public_accueilli) NOT IN {{ get_public_accueilli_exclus() }})
{%- endmacro -%}
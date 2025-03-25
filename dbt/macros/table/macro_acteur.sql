{%- macro acteur(ephemeral_filtered_acteur, propositionservice ) -%}

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
    efa.horaires_osm,
    {{ field_empty('efa.horaires_description') }} AS horaires_description,
    efa.public_accueilli,
    efa.reprise,
    efa.exclusivite_de_reprisereparation,
    efa.uniquement_sur_rdv,
    efa.action_principale_id,
    efa.modifie_le,
    efa.parent_id,
    efa.cree_le,
    efa.statut
FROM {{ ref(ephemeral_filtered_acteur) }} AS efa
INNER JOIN {{ ref(propositionservice) }} AS cps
    ON efa.identifiant_unique = cps.acteur_id
-- filter to apply on resolved parent + children acteur
WHERE (efa.public_accueilli IS NULL OR UPPER(efa.public_accueilli) NOT IN {{ get_public_accueilli_exclus() }})
{%- endmacro -%}
WITH acteur_type_id_to_code AS (
    SELECT
        id,
        code
    FROM {{ ref('base_acteur_type') }}
), source_id_to_code AS (
    SELECT
        id,
        code
    FROM {{ ref('base_source') }}
)

SELECT
    CAST({{ target.schema }}.encode_base57(uuid_generate_v5('6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid, COALESCE(ra.identifiant_unique, a.identifiant_unique)::text)) AS varchar(22)) AS uuid,
    {{ coalesce_empty('ra.identifiant_unique', 'a.identifiant_unique') }} AS identifiant_unique,
    {{ coalesce_empty('ra.nom', 'a.nom') }} AS nom,
    {{ coalesce_empty('ra.description', 'a.description') }} AS description,
    COALESCE(ra.acteur_type_id, a.acteur_type_id) AS acteur_type_id,
    (SELECT code FROM acteur_type_id_to_code WHERE id = COALESCE(ra.acteur_type_id, a.acteur_type_id)) AS acteur_type_code,
    {{ coalesce_empty('ra.adresse', 'a.adresse') }} AS adresse,
    {{ coalesce_empty('ra.adresse_complement', 'a.adresse_complement') }} AS adresse_complement,
    {{ coalesce_empty('ra.code_postal', 'a.code_postal') }} AS code_postal,
    {{ coalesce_empty('ra.ville', 'a.ville') }} AS ville,
    {{ coalesce_empty('ra.url', 'a.url') }} AS url,
    {{ coalesce_empty('ra.email', 'a.email') }} AS email,
    COALESCE(ra.location, a.location) AS location,
    {{ coalesce_empty('ra.telephone', 'a.telephone') }} AS telephone,
    {{ coalesce_empty('ra.nom_commercial', 'a.nom_commercial') }} AS nom_commercial,
    {{ coalesce_empty('ra.nom_officiel', 'a.nom_officiel') }} AS nom_officiel,
    {{ coalesce_empty('ra.siren', 'a.siren') }} AS siren,
    {{ coalesce_empty('ra.siret', 'a.siret') }} AS siret,
    COALESCE(ra.source_id, a.source_id) AS source_id,
    (SELECT code FROM source_id_to_code WHERE id = COALESCE(ra.source_id, a.source_id)) AS source_code,
    {{ coalesce_empty('ra.identifiant_externe', 'a.identifiant_externe') }} AS identifiant_externe,
    {{ coalesce_empty('ra.statut', 'a.statut') }} AS statut,
    {{ coalesce_empty('ra.naf_principal', 'a.naf_principal') }} AS naf_principal,
    {{ coalesce_empty('ra.commentaires', 'a.commentaires') }} AS commentaires,
    {{ coalesce_empty('ra.horaires_osm', 'a.horaires_osm') }} AS horaires_osm,
    {{ coalesce_empty('ra.horaires_description', 'a.horaires_description') }} AS horaires_description,
    {{ coalesce_empty('ra.public_accueilli', 'a.public_accueilli') }} AS public_accueilli,
    {{ coalesce_empty('ra.reprise', 'a.reprise') }} AS reprise,
    COALESCE(ra.exclusivite_de_reprisereparation, a.exclusivite_de_reprisereparation) AS exclusivite_de_reprisereparation,
    COALESCE(ra.uniquement_sur_rdv, a.uniquement_sur_rdv) AS uniquement_sur_rdv,
    COALESCE(ra.action_principale_id, a.action_principale_id) AS action_principale_id,
    COALESCE(ra.modifie_le, a.modifie_le) AS modifie_le,
    ra.parent_id AS parent_id,
    COALESCE(a.cree_le, ra.cree_le) AS cree_le,
    -- avec_revision est true si la table revisionacteur existe
    ra.identifiant_unique IS NOT NULL AS revision_existe
FROM {{ ref('base_acteur') }} AS a
FULL JOIN {{ ref('base_revisionacteur') }} AS ra
  ON a.identifiant_unique = ra.identifiant_unique

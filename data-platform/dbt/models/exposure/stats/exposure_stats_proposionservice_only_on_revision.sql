-- Acteurs dont des propositions de service sont présentes côté révision mais pas côté acteur
-- Colonnes : identifiant_unique, nom, more_propositionservice (JSON), propositionservices (JSON)

WITH revisions AS (
    SELECT DISTINCT identifiant_unique
    FROM {{ ref('marts_acteur_vs_revision_propositon_services') }}
    WHERE source = 'revision'
),

more_props_agg AS (
    SELECT
        m.identifiant_unique,
        a.code AS action_code,
        jsonb_agg(sco.code ORDER BY sco.code) AS sous_categories
    FROM {{ ref('marts_acteur_vs_revision_propositon_services') }} AS m
    INNER JOIN {{ source('qfdmo', 'qfdmo_action') }} AS a ON m.action_id = a.id
    INNER JOIN {{ source('qfdmo', 'qfdmo_souscategorieobjet') }} AS sco ON m.souscategorieobjet_id = sco.id
    WHERE m.source = 'revision'
    GROUP BY m.identifiant_unique, a.code
),

more_propositionservices AS (
    SELECT
        identifiant_unique,
        jsonb_object_agg(action_code, sous_categories) AS more_propositionservices
    FROM more_props_agg
    GROUP BY identifiant_unique
),

revision_props_agg AS (
    SELECT
        rps.acteur_id AS identifiant_unique,
        a.code AS action_code,
        jsonb_agg(DISTINCT sco.code ORDER BY sco.code) AS sous_categories
    FROM {{ ref('int_revisionpropositonservices_with_acteur') }} AS rps
    INNER JOIN {{ ref('int_revisionpropositonservice_sous_categories_with_acteur') }} AS rpsc
        ON rps.id = rpsc.revisionpropositionservice_id
    INNER JOIN {{ source('qfdmo', 'qfdmo_action') }} AS a ON rps.action_id = a.id
    INNER JOIN {{ source('qfdmo', 'qfdmo_souscategorieobjet') }} AS sco
        ON rpsc.souscategorieobjet_id = sco.id
    WHERE rps.acteur_id IN (SELECT identifiant_unique FROM revisions)
    GROUP BY rps.acteur_id, a.code
),

revisionpropositionservices AS (
    SELECT
        identifiant_unique,
        jsonb_object_agg(action_code, sous_categories) AS propositionservices
    FROM revision_props_agg
    GROUP BY identifiant_unique
)

SELECT
    a.identifiant_unique,
    a.nom,
    mp.more_propositionservices,
    ps.propositionservices
FROM revisions AS ao
INNER JOIN {{ ref('int_acteur_with_revision') }} AS a ON ao.identifiant_unique = a.identifiant_unique
INNER JOIN more_propositionservices AS mp ON ao.identifiant_unique = mp.identifiant_unique
INNER JOIN revisionpropositionservices AS ps ON ao.identifiant_unique = ps.identifiant_unique
ORDER BY a.nom, a.identifiant_unique

-- Identifiants uniques pour lesquels les propositions de services diffèrent entre acteur et révision.
-- Compare les paires (action_id, souscategorieobjet_id) côté acteur et côté révision.

WITH acteur_props AS (
    SELECT
        ps.acteur_id AS identifiant_unique,
        ps.action_id,
        souscategorieobjet_id
    FROM {{ ref('int_propositonservices_with_revision') }} AS ps
    INNER JOIN {{ ref('int_propositionservice_sous_categories_with_revision') }} AS psc
        ON ps.id = psc.propositionservice_id
),

revision_props AS (
    SELECT
        rps.acteur_id AS identifiant_unique,
        rps.action_id,
        souscategorieobjet_id
    FROM {{ ref('int_revisionpropositonservices_with_acteur') }} AS rps
    INNER JOIN {{ ref('int_revisionpropositonservice_sous_categories_with_acteur') }} AS rpsc
        ON rps.id = rpsc.revisionpropositionservice_id
),

-- Paires présentes côté acteur mais pas côté révision
diff_acteur_minus_revision AS (
    SELECT DISTINCT identifiant_unique, action_id, souscategorieobjet_id
    FROM (
        (SELECT identifiant_unique, action_id, souscategorieobjet_id FROM acteur_props)
        EXCEPT
        (SELECT identifiant_unique, action_id, souscategorieobjet_id FROM revision_props)
    ) AS t
),

-- Paires présentes côté révision mais pas côté acteur
diff_revision_minus_acteur AS (
    SELECT DISTINCT identifiant_unique, action_id, souscategorieobjet_id
    FROM (
        (SELECT identifiant_unique, action_id, souscategorieobjet_id FROM revision_props)
        EXCEPT
        (SELECT identifiant_unique, action_id, souscategorieobjet_id FROM acteur_props)
    ) AS t
)

SELECT DISTINCT identifiant_unique, action_id, souscategorieobjet_id, source
FROM (
    SELECT identifiant_unique, action_id, souscategorieobjet_id, 'acteur' AS source FROM diff_acteur_minus_revision
    UNION
    SELECT identifiant_unique, action_id, souscategorieobjet_id, 'revision' AS source FROM diff_revision_minus_acteur
) AS u
ORDER BY identifiant_unique, action_id, souscategorieobjet_id

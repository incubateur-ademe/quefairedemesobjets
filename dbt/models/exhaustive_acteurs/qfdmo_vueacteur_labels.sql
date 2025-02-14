WITH acteur_labels AS (
    SELECT
        al.id as id,
        al.acteur_id as vueacteur_id,
        al.labelqualite_id as labelqualite_id
    from qfdmo_acteur_labels al
    inner join dbtvue_acteur as a on al.acteur_id = a.identifiant_unique and a.revision_existe = false
),
revisionacteur_labels AS (
    SELECT
        ral.id as id,
        ral.revisionacteur_id as vueacteur_id,
        ral.labelqualite_id as labelqualite_id
    from qfdmo_revisionacteur_labels ral
    join dbtvue_acteur as a on ral.revisionacteur_id = a.identifiant_unique and a.revision_existe = true
)

SELECT * FROM acteur_labels
UNION ALL
SELECT * FROM revisionacteur_labels
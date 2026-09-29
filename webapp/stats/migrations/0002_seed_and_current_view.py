from django.db import migrations

# Series of the Metabase dashboard "Suivi des résultats clés KR 2026".
# Ratios (retours support / vues acteurs, budget / visiteurs orientés) are
# computed in Metabase from two series. PostHog insights are picked in the
# Wagtail admin.
KEY_RESULTS = [
    # code, title, target, source, aggregation
    ("visiteurs_orientes", "Visiteurs orientés", 1_500_000, "posthog", "sum_year"),
    ("clics_google", "Clics depuis Google", 500_000, "manual", "sum_year"),
    (
        "reutilisation_donnees_ouvertes",
        "Réutilisation des données ouvertes (appels API + téléchargements)",
        475_000,
        "manual",
        "sum_year",
    ),
    (
        "part_acteurs_siret_siren",
        "Part des acteurs ouverts avec SIRET/SIREN",
        0.8,
        "code",
        "last",
    ),
    (
        "taux_comprehension_nouvelles_fiches",
        "Taux de compréhension – nouvelles fiches",
        None,
        "manual",
        "last",
    ),
    (
        "taux_comprehension_anciennes_fiches",
        "Taux de compréhension – anciennes fiches",
        None,
        "manual",
        "last",
    ),
    (
        "retours_support_lieu_ferme",
        "Retours support sur lieu fermé",
        None,
        "manual",
        "last",
    ),
    ("vues_acteurs", "Vues de fiches acteurs", None, "manual", "last"),
    ("budget", "Budget annuel", None, "manual", "last"),
    ("score_rgaa", "Score RGAA", 100, "manual", "last"),
    ("indice_cyber_anssi", "Indice cyber ANSSI", None, "manual", "last"),
    ("score_fruggr", "Score Fruggr", 80, "manual", "last"),
]

# The current figure of each key result, for Metabase progress cards.
# ponytail: a view means ALTER COLUMN on stats_keyresult needs DROP/CREATE
# VIEW around it in the migration.
CREATE_VIEW = """
CREATE VIEW stats_keyresult_current AS
SELECT *, CASE WHEN target > 0 THEN current_value / target END AS progress
FROM (
    SELECT kr.id, kr.code, kr.title, kr.description, kr.target, kr.source,
        kr.aggregation,
        CASE kr.aggregation
            WHEN 'sum_year' THEN (
                SELECT SUM(v.value) FROM stats_keyresultvalue v
                WHERE v.key_result_id = kr.id
                AND v.date >= date_trunc('year', CURRENT_DATE)
            )
            ELSE (
                SELECT v.value FROM stats_keyresultvalue v
                WHERE v.key_result_id = kr.id ORDER BY v.date DESC LIMIT 1
            )
        END AS current_value,
        (SELECT MAX(v.date) FROM stats_keyresultvalue v
         WHERE v.key_result_id = kr.id) AS last_date
    FROM stats_keyresult kr
) current
"""


def seed(apps, schema_editor):
    KeyResult = apps.get_model("stats", "KeyResult")
    for code, title, target, source, aggregation in KEY_RESULTS:
        KeyResult.objects.get_or_create(
            code=code,
            defaults={
                "title": title,
                "target": target,
                "source": source,
                "aggregation": aggregation,
            },
        )


class Migration(migrations.Migration):
    dependencies = [("stats", "0001_initial")]
    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
        migrations.RunSQL(CREATE_VIEW, "DROP VIEW stats_keyresult_current"),
    ]

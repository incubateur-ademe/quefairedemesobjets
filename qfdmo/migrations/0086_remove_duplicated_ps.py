# Generated by Django 5.0.4 on 2024-07-25 08:22

from django.db import migrations, transaction
from django.db.models import Count


def merge_ps_actions(apps, schema_editor):
    PropositionService = apps.get_model("qfdmo", "PropositionService")
    RevisionPropositionService = apps.get_model("qfdmo", "RevisionPropositionService")
    DisplayedPropositionService = apps.get_model("qfdmo", "DisplayedPropositionService")

    for cls in [
        PropositionService,
        RevisionPropositionService,
        DisplayedPropositionService,
    ]:
        for duplicated_pss in (
            cls.objects.values("action_id", "acteur_id")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        ):
            pss = cls.objects.prefetch_related("sous_categories").filter(
                action_id=duplicated_pss["action_id"],
                acteur_id=duplicated_pss["acteur_id"],
            )
            sous_categories = list(
                set([sc for p in pss for sc in p.sous_categories.all()])
            )
            with transaction.atomic():

                pss.delete()
                ps = cls.objects.create(
                    action_id=duplicated_pss["action_id"],
                    acteur_id=duplicated_pss["acteur_id"],
                )
                ps.sous_categories.add(*sous_categories)


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0085_alter_acteur_acteur_services_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            f"""
                SELECT setval(pg_get_serial_sequence('"qfdmo_displayedpropositionservice"', 'id'),
                COALESCE(MAX(id), 1), max(id) IS NOT null) FROM "qfdmo_displayedpropositionservice";
            """,
            migrations.RunSQL.noop,
        ),
        migrations.RunPython(
            merge_ps_actions,
            migrations.RunPython.noop,
        ),
    ]

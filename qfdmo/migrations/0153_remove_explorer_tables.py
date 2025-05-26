from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0152_schema_warehouse"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DROP TABLE IF EXISTS explorer_databaseconnection CASCADE;
            DROP TABLE IF EXISTS explorer_explorervalue CASCADE;
            DROP TABLE IF EXISTS explorer_promptlog CASCADE;
            DROP TABLE IF EXISTS explorer_query CASCADE;
            DROP TABLE IF EXISTS explorer_queryfavorite CASCADE;
            DROP TABLE IF EXISTS explorer_querylog CASCADE;
            DROP TABLE IF EXISTS explorer_tabledescription CASCADE;
            """,
            reverse_sql="",
        ),
    ]

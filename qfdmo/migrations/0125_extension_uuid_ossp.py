# Generated by Django 5.1.5 on 2025-02-18 12:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0124_remove_dagrunchange_dag_run_delete_dagrun_and_more"),
    ]

    operations = [migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')]

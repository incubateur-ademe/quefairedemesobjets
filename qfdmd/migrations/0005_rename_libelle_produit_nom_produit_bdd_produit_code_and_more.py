# Generated by Django 5.1.1 on 2024-11-04 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0004_remove_produit_titre_produit_libelle_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="produit",
            options={},
        ),
        migrations.RenameField(
            model_name="produit",
            old_name="libelle",
            new_name="nom",
        ),
        migrations.AddField(
            model_name="produit",
            name="bdd",
            field=models.CharField(blank=True, help_text="Bdd"),
        ),
        migrations.AddField(
            model_name="produit",
            name="code",
            field=models.CharField(blank=True, help_text="Code"),
        ),
        migrations.AddField(
            model_name="produit",
            name="comment_les_eviter",
            field=models.TextField(blank=True, help_text="Comment les éviter ?"),
        ),
        migrations.AddField(
            model_name="produit",
            name="filieres_rep",
            field=models.TextField(blank=True, help_text="Filière(s) REP concernée(s)"),
        ),
        migrations.AddField(
            model_name="produit",
            name="nom_eco_organisme",
            field=models.TextField(blank=True, help_text="Nom de l’éco-organisme"),
        ),
        migrations.AddField(
            model_name="produit",
            name="qu_est_ce_que_j_en_fais",
            field=models.TextField(blank=True, help_text="Qu'est-ce que j'en fais ?"),
        ),
        migrations.AddField(
            model_name="produit",
            name="que_va_t_il_devenir",
            field=models.TextField(blank=True, help_text="Que va-t-il devenir ?"),
        ),
        migrations.AddField(
            model_name="produit",
            name="slug",
            field=models.CharField(blank=True, help_text="Slug - ne pas modifier"),
        ),
        migrations.AddField(
            model_name="produit",
            name="synonymes_existants",
            field=models.TextField(blank=True, help_text="Synonymes existants"),
        ),
    ]

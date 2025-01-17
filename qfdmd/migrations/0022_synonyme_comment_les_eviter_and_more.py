# Generated by Django 5.1.1 on 2024-12-19 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "qfdmd",
            "0015_remove_produit_picto_synonyme_picto_squashed_0021_alter_synonyme_picto",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="synonyme",
            name="comment_les_eviter",
            field=models.TextField(
                blank=True, help_text="Comment consommer responsable ?"
            ),
        ),
        migrations.AddField(
            model_name="synonyme",
            name="qu_est_ce_que_j_en_fais_bon_etat",
            field=models.TextField(
                blank=True, help_text="Qu'est-ce que j'en fais ? - Bon état"
            ),
        ),
        migrations.AddField(
            model_name="synonyme",
            name="qu_est_ce_que_j_en_fais_mauvais_etat",
            field=models.TextField(
                blank=True, help_text="Qu'est-ce que j'en fais ? - Mauvais état"
            ),
        ),
        migrations.AddField(
            model_name="synonyme",
            name="que_va_t_il_devenir",
            field=models.TextField(blank=True, help_text="Que va-t-il devenir ?"),
        ),
    ]

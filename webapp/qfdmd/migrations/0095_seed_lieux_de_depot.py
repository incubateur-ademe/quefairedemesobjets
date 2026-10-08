# The lieux de dépôt the fiches already name in their badges (census of the
# first row of cards of the 45 live fiches, 2026-09-28), with the badge
# colour each one wears there. Editable in the CMS afterwards; existing codes
# are left as they are.

from django.db import migrations

LIEUX = [
    ("bac_de_tri", "Bac de tri", "yellow-tournesol"),
    ("conteneur_a_verre", "Conteneur à verre", "green-emeraude"),
    ("decheterie", "Déchèterie", "brown-caramel"),
    ("point_de_collecte", "Point de collecte", "blue-ecume"),
    ("ordures_menageres", "Ordures ménagères", "orange-terre-battue"),
    ("magasin", "Magasin", "pink-macaron"),
    ("bac_de_compostage", "Bac de compostage", "brown-caramel"),
    ("bois_de_chauffage", "Bois de chauffage", "orange-terre-battue"),
    ("entre_particuliers", "Entre particuliers", "beige-gris-galet"),
    ("reemploi", "Réemploi", "blue-cumulus"),
    ("structure_de_reemploi", "Structure de réemploi", "green-emeraude"),
    ("etablissement_de_sante", "Établissement de santé", "green-bourgeon"),
]


def seed(apps, schema_editor):
    LieuDeDepot = apps.get_model("qfdmd", "LieuDeDepot")
    for code, libelle, couleur in LIEUX:
        LieuDeDepot.objects.get_or_create(
            code=code, defaults={"libelle": libelle, "couleur": couleur}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmd", "0094_lieudedepot_and_consignes_block"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]

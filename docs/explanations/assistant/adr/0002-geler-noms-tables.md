# Décision 0002 : geler les noms de tables lors du renommage des apps

Date : 2026-09-12

## Statut

Proposé

## Contexte

Les apps Django `qfdmd` et `qfdmo` portent des noms opaques, hérités de
l'histoire du projet. On souhaite les renommer en `quefaire` et `acteur`.

Mesure de l'impact sur la base actuelle :

```text
webapp        : ~3050 occurrences « qfdmd », ~3040 « qfdmo »
migrations    : 57 + 38 = 95
data-platform : 106 fichiers (DAGs Airflow, tests, Dockerfiles)
dbt           : 38 fichiers référençant les tables physiques
```

**Constat déterminant** : aucun modèle des deux apps ne déclare `db_table`. Les
tables portent donc le nom par défaut de Django, `<app_label>_<model>` :
`qfdmo_displayedacteur`, `qfdmd_produitpage`, etc.

Conséquence : renommer les apps renommerait **~95 tables**, que la
data-platform lit directement (dbt via `ref_table`, DAGs Airflow via des
requêtes SQL).

## Décision

On renomme **le code** (`qfdmd` → `quefaire`, `qfdmo` → `acteur`) et on **fige
les noms de tables** à leur valeur historique via un `db_table` explicite sur
chaque modèle :

```python
class DisplayedActeur(...):
    class Meta:
        db_table = "qfdmo_displayedacteur"   # nom historique, figé
```

Chaque `models.py` porte un commentaire d'en-tête expliquant la divergence.

Une data migration met à jour `django_content_type.app_label`, sans quoi les
pages Wagtail existantes ne se résolvent plus (`Page.specific` passe par le
ContentType).

Un test permanent garantit qu'aucun modèle n'échappe à la règle :

```python
def test_every_model_declares_db_table():
    for app_label in ("acteur", "quefaire"):
        for modele in apps.get_app_config(app_label).get_models():
            assert "db_table" in modele.Meta.__dict__ or modele._meta.proxy, modele
```

## Alternatives écartées

### Renommer aussi les tables

Imposerait une migration coordonnée webapp + Airflow + dbt, avec fenêtre
d'indisponibilité et risque de perte de données, pour un gain purement
cosmétique sur des noms que seule la data-platform manipule. **Écarté.**

### Ne pas renommer les apps

Laisserait l'assistant V2 importer `qfdmo.DisplayedActeur`, c'est-à-dire
construire du neuf sur une nomenclature qu'on juge illisible. **Écarté** : le
coût du renommage est ponctuel, celui de l'opacité est permanent.

## Conséquences

### Positives

- **Zéro migration de données**, zéro downtime, aucun risque de perte.
- **data-platform et dbt intacts** : aucun fichier à modifier de leur côté.
- Le code applicatif gagne des noms lisibles.
- Réversible : le renommage est un `git revert` tant que les tables ne bougent pas.

### Négatives

- **Les noms d'app et de table divergent durablement** :
  `acteur.DisplayedActeur` vit dans `qfdmo_displayedacteur`. C'est surprenant
  pour qui découvre le projet, d'où le commentaire d'en-tête obligatoire et
  cette ADR.
- Une ligne `Meta.db_table` à ne pas oublier sur chaque nouveau modèle des deux
  apps — couvert par le test permanent.

### Neutres

- Si un jour la data-platform devait être migrée pour d'autres raisons, ce
  serait l'occasion d'aligner les noms de tables. Cette ADR serait alors
  remplacée.

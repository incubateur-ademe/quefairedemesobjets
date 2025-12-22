# Commandes Django d'administration

## Correction de la valeur d'un champs sur toute la base d'acteur

Cas d'utilisation : quand un groupe d'acteur conséquent a une valeur fausse et qu'on souhaite la corriger en masse.

Étape du script :

- Recherche la valeur à corriger parmis tous les acteurs compilés (VueActeur)
- Créer une révision si elle n'existe pas pour chaque acteur à corriger
- modifie la valeur du champ de la révision pour chaque acteur à corriger

Note: il existe une option `--dry-run` permettant de visualiser la correction avant de l'appliquer

```sh
(uv run) python manage.py correction_acteur_field --field champ_a_modifier --old_value "valeur à corriger" --new_value "Remplacer par cette valeur" (--dry-run)
```

ex d'utilisation

```sh
uv run python manage.py correction_acteur_field --field horaires_osm --old_value "Mo off; Tu off; We off; Th off; Fr off; Sa off; Su off" --new_value __empty__ --dry-run
```

## Population des propositions de service avec une sous-catégorie

Ajout d'une sous-catégorie aux propositions de service qui en contient une autre

Cette commande est utile quand on ajoute une nouvelle sous-catégorie car on a besoin de plus de détails, on veut alors pouvoir ajouter cette nouvelle sous-catégorie en masse aux propositions de service qui en contient une sous-catégorie spécifique.

```sh
(uv run) python manage.py populate_propositionservice --new_sous_categorie_code sous_categorie_a_populer --origin_sous_categorie_code sous_categorie_pour_identifier_les_propositions_de_service_a_populer (--dry-run)
```

Par exemple : on souhaite ajouter la sous-catégorie "Poêle et Casserole" aux propositions de service qui en contiennent la sous-catégorie "Vaisselle"

```sh
uv run python manage.py populate_propositionservice --new_sous_categorie_code poele_casserole --origin_sous_categorie_code vaisselle --dry-run
```

## Génération des variables d'environnement pour les logs Airflow sur S3

Cette commande génère les variables d'environnement nécessaires pour configurer le stockage des logs Airflow sur un bucket S3 compatible (Scaleway Object Storage).

La commande crée une connexion AWS Airflow et affiche toutes les variables d'environnement à ajouter à votre configuration pour activer le logging distant sur S3.

```sh
(uv run) python manage.py generate_aws_conn_id_env --access_key ACCESS_KEY --secret_key SECRET_KEY --bucket_name BUCKET_NAME --conn_id CONN_ID
```

**Arguments :**

- `--access_key` (requis) : Clé d'accès AWS/S3 (login)
- `--secret_key` (requis) : Clé secrète AWS/S3 (password)
- `--bucket_name` (optionnel) : Nom du bucket S3 (défaut: `qfdmo-airflow-logs`)
- `--conn_id` (optionnel) : ID de la connexion Airflow (défaut: `log_default`)

**Exemple d'utilisation :**

```sh
uv run python manage.py generate_aws_conn_id_env --access_key ACCESS_KEY --secret_key SECRET_KEY --bucket_name lvao-dev-airflow --conn_id log_conn_id
```

La commande affichera les variables d'environnement à copier dans votre configuration (`.env`, fichier de configuration Docker, etc.).

# Créaton d'un base de données sur Scaleway

## Création d'une base de données via l'interface

[Console Scaleway](https://console.scaleway.com)

### Prérequis

Prévenir le.a référent.e technique de l'ADEME de l'évolution de la stack pour éviter les surprises sur la facture

### Créer l'instance de base de données managées

Dans la section `Databases` > `… PostgreSQL …`, Créer une nouvelle base de données. \
Localiser la DB en France \
Préférer une base de données cryptées \
Choisir 15 K IOPS pour des besoins intensifs (data) et choisir le plan en fonction des besoins \
Nommer la base de données selon les conventions définies avec l'équipe technique (voir [Infrastructure](../../reference/infrastructure/README.md)).

### Créer la base de données

Dans l'onglet `Databases`, créer la base de données (ex: `qfdmo`) |
Dans l'onglet `Users`, permettre aux utilisateur d'administrer la base de données

### Tester l'accès à la base de données

```sh
psql -d 'postgres://<user>:<password>@<host>:<port>/<database>?sslmode=require'
```

### Créer les extensions et les schema

Si nécessaire, créer les schema et exetensions en utilisant les scripts

```sh
psql -d 'postgres://<user>:<password>@<host>:<port>/<database>?sslmode=require' < scripts/sql/create_extensions.sql
psql -d 'postgres://<user>:<password>@<host>:<port>/<database>?sslmode=require' < scripts/sql/create_schema.sql
```

## Restaurer un backup de base de données

Récupérer le backup le plus à jour \
Puis lancer la restauration (l'option `schema` permet de restaurer uniquement le schema précisé) :

```sh
pg_restore -d 'postgres://<user>:<password>@<host>:<port>/<database>?sslmode=require' --schema=public --clean --no-acl --no-owner --no-privileges <FILE>.pgsql
```

## Mise à jour des environnements

Pour chacune des instances de l'environnement, aller mettre à jour les variables d'environnement et redémarrer les instances:

- webapp quefairedemesobjets
- airflow-webserver
- airflow-scheduler
- metabase

Tester et constater que la nouvelle base de données est utilsée

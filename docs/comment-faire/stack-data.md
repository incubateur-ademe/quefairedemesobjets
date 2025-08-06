# Mise en place de la stack data en local

La stack data nécessite un certain nombre d'opérations manuelles en local afin d'être opérationnelle.
En vrac (non exhaustif):

- Ingestion de sources
- Ingestion de la base d'adresses nationales
- Ingestion d'annuaire entreprise

## Mise en place de la base de données

La base de données nécessite certaines tables en base avant de pouvoir fonctionner avec `dbt` :

- `poetry run python manage.py create_remote_db_server`

## Ingestion de sources

Une source peut être ingéré en lancant le DAG correspondant.

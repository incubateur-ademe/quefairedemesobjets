# Prérequis concernant les bases de données

## Versions

On essayera autant que possible d'être à jour des versions majeur des base de données

## Base de données

On utilise 2 bases de données :

- `qfdmo` : pour la webbapp
- `warehouse` : pour le travail de data

## Extensions

Les extensions postgresql utilisées sont :

- postgis
- pg_stat_statements
- unaccent
- pg_trgm
- uuid-ossp
- postgres_fdw

Celles-ci sont ré-installées lors de la restauration de la base de données car la suppression/restauration du schema public ne recrée pas ces extensions (cf. [./scripts/sql/create_extensions.sql](../../../scripts/sql/create_extensions.sql))

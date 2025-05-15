# Prérequis concernant les bases de données

## Versions

On essayera autant que possible d'être à jour des versions majeur des base de données

## Extensions

Les extensions postgresql utilisées sont :

- postgis
- pg_stat_statements
- unaccent
- pg_trgm
- uuid-ossp

Celles-ci sont ré-installées lors de la restauration de la base de données car la suppression/restauration du schema public ne recrée pas ces extensions (cf. [./scripts/sql/create_extensions.sql](./scripts/sql/create_extensions.sql))

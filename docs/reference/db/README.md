# Postgresql Database

This project uses **PostgreSQL** as the main database engine for both the web application and the data platform.

## Versions

We try to stay up to date with the latest **major versions** of PostgreSQL, without breaking compatibility with our frameworks and libraries.

## Databases

We currently use **multiple PostgreSQL databases**

For more details, read [db_organisation.md](./db_organisation.md)

## PostgreSQL extensions

We rely on several **PostgreSQL extensions**:

- `postgis`: spatial / GIS support for geographic data (used for locations, maps, distance computations, etc.).
- `pg_stat_statements`: query statistics to monitor and optimize SQL performance.
- `unaccent`: accent-insensitive text search and comparisons.
- `pg_trgm`: trigram-based text similarity and fuzzy search (for example for suggestions and search-as-you-type).
- `uuid-ossp`: generation of UUID identifiers in PostgreSQL.
- `postgres_fdw`: foreign data wrapper to read data from other PostgreSQL servers or databases.

These extensions are (re)created automatically by a SQL script when restoring the database, because dropping/restoring the `public` schema does **not** recreate the extensions: [`scripts/sql/create_extensions.sql`](../../../scripts/sql/create_extensions.sql).

If you add new features that depend on PostgreSQL extensions, update both:

- this documentation file, to explain what the extension is used for, and
- the `create_extensions.sql` script, to ensure the extension is installed in new environments and during restores.

## Handling default values in the database

### String fields

For fields of type string that must not be nullable, the default value is an empty string, as indicated in the Django documentation: [https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options](https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options)

### Boolean fields

Boolean fields can have a null value, which means that the information is unknown.

Example: `uniquement_sur_rdv`: `True` / `False` / `None` → Yes / No / We do not have this information

## Using SQL constraints

We use SQL constraints to enforce data quality criteria. These constraints must be implemented via Django models (the [`Meta.constraints` option](https://docs.djangoproject.com/en/5.1/ref/models/options/#django.db.models.Options.constraints)). See the [initial proposal](https://github.com/incubateur-ademe/quefairedemesobjets/pull/1227).

### Conditional constraints

We also use conditional constraints, for example, the uniqueness of the (`source_id`, `external_identifier`) pair for `active` actors only.

## Architecture

More about architecture of data in `webapp` database

```{toctree}
:maxdepth: 2

db_organisation.md
architecture.md
```

# dbt Documentation

Production-ready patterns for dbt (data build tool) including model organization, testing strategies, documentation, and incremental processing.

## Model Layers

```
source/           Source definitions (YAML only, declares external tables)
    ↓
base/             1:1 with source, light cleaning / filtering
    ↓
intermediate/     Business logic, joins, aggregations, normalisation
    ↓
marts/            Business-ready models (combines intermediate models)
    ↓
exposure/         Final tables exposed to consumers (API, dashboards, Open Data)
```

## Naming Conventions

| Layer        | Prefix      | Example                                     |
| ------------ | ----------- | ------------------------------------------- |
| Source       | `source_`   | `source_stats.yml`                          |
| Base         | `base_`     | `base_vueacteur_visible.sql`                |
| Intermediate | `int_`      | `int_acteur_visible_location.sql`           |
| Marts        | `marts_`    | `marts_acteur_stacked.sql`                  |
| Exposure     | `exposure_` | `exposure_stats_acteur_stacked_history.sql` |

Each layer is organized by **subject** (business domain): `acteurs`, `stats`, `geo`, `ban`, `ae_annuaire_entreprises`, `enrich`.

## Project Structure

```
data-platform/dbt/
├── dbt_project.yml
├── Makefile
├── macros/
│   ├── field/                           Field-level helpers
│   │   ├── acteur_status_is_active.sql
│   │   ├── coalesce_empty.sql
│   │   ├── field_empty.sql
│   │   └── sscat_from_action.sql
│   ├── table/                           Table-level macros (reusable model logic)
│   │   ├── macro_acteur.sql
│   │   ├── macro_acteur_sources.sql
│   │   ├── macro_acteur_labels.sql
│   │   ├── macro_acteur_epci.sql
│   │   ├── macro_propositionservice.sql
│   │   └── ...
│   ├── udf/                             User-defined functions (created on-run-start)
│   │   ├── udf_encode_base57.sql
│   │   ├── udf_uuid_to_int.sql
│   │   └── ...
│   └── constants/                       Shared constants
│       ├── value_unavailable.sql
│       └── public_accueilli_exclus.sql
└── models/
    ├── source/                          Source definitions (YAML only)
    │   ├── source_acteur.yml
    │   ├── source_stats.yml
    │   ├── source_ban_base_adresse_nationale.yml
    │   ├── source_ae_annuaire_entreprises.yml
    │   └── source_enrich.yml
    ├── base/                            1:1 with source, light cleaning
    │   ├── acteurs/
    │   │   ├── schema.yml
    │   │   ├── base_acteur.sql
    │   │   ├── base_acteur_acteur_services.sql
    │   │   ├── base_propositionservice.sql
    │   │   └── base_source.sql
    │   ├── stats/
    │   │   ├── schema.yml
    │   │   ├── base_action.sql
    │   │   ├── base_vueacteur_visible.sql
    │   │   ├── base_vuepropositionservice.sql
    │   │   ├── base_vuepropositionservice_visible.sql
    │   │   └── base_random_position.sql
    │   ├── ban/
    │   │   ├── schema.yml
    │   │   ├── base_ban_adresses.sql
    │   │   └── base_ban_lieux_dits.sql
    │   └── ae_annuaire_entreprises/
    │       ├── schema.yml
    │       ├── base_ae_unite_legale.sql
    │       └── base_ae_etablissement.sql
    ├── intermediate/                    Business logic, joins, aggregations
    │   ├── acteurs/
    │   │   ├── schema.yml
    │   │   └── int_acteur.sql
    │   ├── stats/
    │   │   ├── schema.yml
    │   │   ├── int_acteur_visible_location.sql
    │   │   ├── int_acteur_visible_location_rounded.sql
    │   │   ├── int_acteur_with_siren.sql
    │   │   ├── int_acteur_with_siret.sql
    │   │   ├── int_acteur_with_revision.sql
    │   │   ├── int_stacked_location.sql
    │   │   └── int_stacked_location_rounded.sql
    │   ├── geo/
    │   │   ├── schema.yml
    │   │   └── int_epci.sql
    │   ├── ban/
    │   │   ├── int_ban_adresses.sql
    │   │   └── int_ban_villes.sql
    │   └── ae_annuaire_entreprises/
    │       ├── schema.yml
    │       ├── int_ae_unite_legale.sql
    │       └── int_ae_etablissement.sql
    ├── marts/                           Business-ready models
    │   ├── acteurs/
    │   │   ├── carte/                   Models for the map (carte)
    │   │   │   ├── schema.yml
    │   │   │   ├── marts_carte_acteur.sql
    │   │   │   └── ...
    │   │   ├── opendata/                Models for Open Data export
    │   │   │   ├── schema.yml
    │   │   │   ├── marts_opendata_acteur.sql
    │   │   │   └── ...
    │   │   ├── exhaustive/              All acteurs without filtering
    │   │   │   └── ...
    │   │   └── sample/                  Sample/displayed acteurs
    │   │       └── ...
    │   ├── stats/                       Statistics and metrics
    │   │   ├── schema.yml
    │   │   ├── marts_acteur_stacked.sql
    │   │   ├── marts_acteur_siren_actif.sql
    │   │   ├── marts_distance_first_action.sql
    │   │   └── ...
    │   └── enrich/                      Data enrichment suggestions
    │       ├── schema.yml
    │       ├── marts_enrich_acteurs_closed_candidates.sql
    │       └── ...
    └── exposure/                        Final tables exposed to consumers
        ├── acteurs/
        │   ├── carte/
        │   │   ├── schema.yml
        │   │   └── exposure_carte_acteur.sql
        │   ├── opendata/
        │   │   └── schema.yml
        │   ├── exhaustive/
        │   │   └── ...
        │   └── sample/
        │       └── ...
        ├── stats/
        │   ├── schema.yml
        │   ├── exposure_stats_acteur_stacked_history.sql
        │   ├── exposure_stats_acteur_no_siren_actif.sql
        │   ├── exposure_stats_distance_nb_acteur_by_action.sql
        │   └── ...
        └── geo/
            ├── schema.yml
            └── exposure_epci.sql
```

## Patterns

All examples below use real models from the `stats` subject.

### Pattern 1: Source Definitions

Sources are declared in YAML files in `models/source/`. Each source maps to a database schema.

```yaml
# models/source/source_stats.yml
version: 2

sources:
  - name: stats_qfdmo
    schema: webapp_public
    tables:
      - name: qfdmo_vueacteur
      - name: qfdmo_vuepropositionservice
      - name: qfdmo_action
  - name: stats_clone
    schema: public
    tables:
      - name: clone_ca_epci_in_use
      - name: clone_ae_unite_legale_in_use
      - name: clone_ae_etablissement_in_use
```

### Pattern 2: Base Models

Base models are 1:1 with source tables. They apply minimal transformations: filtering, sampling.

```sql
-- models/base/stats/base_vueacteur_visible.sql
SELECT *
FROM {{ source('stats_qfdmo', 'qfdmo_vueacteur') }}
WHERE est_dans_carte IS TRUE OR est_dans_opendata IS TRUE
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
TABLESAMPLE SYSTEM (10)
{% endif %}
```

```sql
-- models/base/stats/base_action.sql
SELECT *
FROM {{ source('stats_qfdmo', 'qfdmo_action') }}
```

Base models that combine two base models with a simple join are also acceptable:

```sql
-- models/base/stats/base_vuepropositionservice_visible.sql
SELECT *
FROM {{ ref('base_vuepropositionservice') }} AS propositionservice
INNER JOIN {{ ref('base_vueacteur_visible') }} AS acteur
    ON propositionservice.acteur_id = acteur.identifiant_unique
```

### Pattern 3: Intermediate Models

Intermediate models apply business logic: filtering, validation, rounding, aggregation.

```sql
-- models/intermediate/stats/int_acteur_visible_location.sql
SELECT identifiant_unique, latitude, longitude
FROM {{ ref('base_vueacteur_visible') }}
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
AND latitude != 0 AND longitude != 0
```

```sql
-- models/intermediate/stats/int_acteur_with_siret.sql
SELECT identifiant_unique, siret
FROM {{ ref('base_vueacteur_visible') }}
WHERE LENGTH(siret) = 14
AND siret ~ '^[0-9]+$'
```

```sql
-- models/intermediate/stats/int_stacked_location.sql
SELECT latitude, longitude
FROM {{ ref('int_acteur_visible_location') }}
GROUP BY latitude, longitude
HAVING COUNT(*) > 1
```

### Pattern 4: Marts Models

Marts models combine intermediate models to produce business-ready datasets.

```sql
-- models/marts/stats/marts_acteur_stacked.sql
SELECT a.identifiant_unique, a.latitude, a.longitude
FROM {{ ref('int_acteur_visible_location') }} a
INNER JOIN {{ ref('int_stacked_location') }} c
    ON a.latitude = c.latitude
    AND a.longitude = c.longitude
ORDER BY a.latitude, a.longitude, a.identifiant_unique
```

```sql
-- models/marts/stats/marts_acteur_siren_actif.sql
SELECT a.identifiant_unique
FROM {{ ref('int_acteur_with_siren') }} a
INNER JOIN {{ ref('int_ae_siren_in_acteur') }} ae ON a.siren = ae.siren
WHERE ae.etat_administratif = 'A'
```

### Pattern 5: Exposure Models

Exposure models are the final tables exposed to consumers. They can be simple pass-throughs or incremental models that track history.

Simple pass-through:

```sql
-- models/exposure/stats/exposure_stats_acteur_no_siren_actif.sql
select * from {{ ref('marts_acteur_no_siren_actif') }}
```

Exposure with filtering/projection:

```sql
-- models/exposure/stats/exposure_stats_acteur_revision_siren.sql
SELECT
  identifiant_unique,
  nom,
  source_code,
  acteur_siren,
  revision_siren,
  acteur_modifie_le,
  revision_modifie_le
FROM {{ ref('marts_acteur_revision') }}
WHERE revision_siren != ''
AND acteur_siren != ''
AND acteur_statut = 'ACTIF'
AND revision_statut = 'ACTIF'
AND revision_siren != acteur_siren
AND revision_modifie_le < acteur_modifie_le
```

Incremental exposure (history tracking):

```sql
-- models/exposure/stats/exposure_stats_acteur_stacked_history.sql
WITH stacked AS (
    SELECT COUNT(*) AS nb_stacked
    FROM {{ ref('marts_acteur_stacked') }}
),
stacked_rounded AS (
    SELECT COUNT(*) AS nb_stacked_rounded
    FROM {{ ref('marts_acteur_stacked_rounded') }}
),
visible AS (
    SELECT COUNT(*) AS nb_total
    FROM {{ ref('int_acteur_visible_location') }}
)
SELECT
    CURRENT_DATE AS date_snapshot,
    v.nb_total,
    s.nb_stacked,
    sr.nb_stacked_rounded,
    CASE
        WHEN v.nb_total = 0 THEN 0
        ELSE ROUND((s.nb_stacked::NUMERIC / v.nb_total) * 100, 2)
    END AS rate_stacked,
    CASE
        WHEN v.nb_total = 0 THEN 0
        ELSE ROUND((sr.nb_stacked_rounded::NUMERIC / v.nb_total) * 100, 2)
    END AS rate_stacked_rounded
FROM visible v
CROSS JOIN stacked s
CROSS JOIN stacked_rounded sr
```

### Pattern 6: Schema & Testing

Each folder contains a `schema.yml` that documents and tests models.

```yaml
# models/base/stats/schema.yml
version: 2

models:
  - name: base_vueacteur_visible
    description: "Acteurs visibles"
    columns:
      - name: identifiant_unique
        description: "L'identifiant unique de l'acteur"
        data_tests:
          - not_null
          - unique
      - name: nom
        description: "Le nom de l'acteur"
        data_tests:
          - not_null
    config:
      materialized: table
      unique_key: identifiant_unique
      tags:
        - stats
        - base
        - acteurs
        - visible
```

Incremental exposure models use `delete+insert` strategy:

```yaml
# models/exposure/stats/schema.yml (extract)
- name: exposure_stats_acteur_stacked_history
  description: "Historique du nombre d'acteurs empilés"
  columns:
    - name: date_snapshot
      description: "Date de l'exécution dbt"
      data_tests:
        - not_null
        - unique
    - name: nb_total
      data_tests:
        - not_null
  config:
    materialized: incremental
    unique_key: date_snapshot
    incremental_strategy: delete+insert
    tags:
      - exposure
      - stats
```

### Pattern 7: Sampling in Dev

Use the `DBT_SAMPLING` environment variable to limit data in development:

```sql
SELECT *
FROM {{ source('stats_qfdmo', 'qfdmo_vueacteur') }}
WHERE est_dans_carte IS TRUE OR est_dans_opendata IS TRUE
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
TABLESAMPLE SYSTEM (10)
{% endif %}
```

### Pattern 8: UDFs (User-Defined Functions)

UDFs are created automatically at the start of each dbt run via `on-run-start` in `dbt_project.yml`:

```yaml
# dbt_project.yml (extract)
on-run-start:
  - "{{ create_udf_encode_base57() }}"
  - "{{ create_udf_uuid_to_int() }}"
  - "{{ create_udf_safe_divmod() }}"
  - "{{ create_udf_normalize_string_alpha_for_match() }}"
  - "{{ create_udf_ae_string_cleanup() }}"
```

UDF macros live in `macros/udf/`.

## Makefile Commands

Run these commands from `data-platform/dbt/`:

```bash
make generate-docs    # Generate dbt documentation (HTML)
make serve-docs       # Serve documentation locally on port 8085
make clean-docs       # Remove generated documentation (target/)
```

These commands use `uv run dbt` to ensure the correct Python environment.

## dbt Commands

```bash
# Run models
uv run dbt run                              # Run all models
uv run dbt run --select stats               # Run all stats models
uv run dbt run --select +marts_acteur_stacked  # Run model and its upstream dependencies
uv run dbt run --select marts_acteur_stacked+  # Run model and its downstream dependents
uv run dbt run --full-refresh               # Rebuild incremental models from scratch
uv run dbt run --select tag:stats           # Run models tagged "stats"

# Testing
uv run dbt test                             # Run all tests
uv run dbt test --select stats              # Test stats models only
uv run dbt build                            # Run + test in DAG order

# Documentation
uv run dbt docs generate                    # Generate docs
uv run dbt docs serve                       # Serve docs locally

# Debugging
uv run dbt compile                          # Compile SQL without running
uv run dbt debug                            # Test database connection
uv run dbt ls --select tag:stats            # List models by tag

# Sampling (dev only, reduces dataset to ~10%)
DBT_SAMPLING=true uv run dbt run
```

## Data Flow Example: Stats Stacked Acteurs

```
source_stats.yml (qfdmo_vueacteur)
    ↓
base_vueacteur_visible.sql          (filter: visible acteurs only)
    ↓
int_acteur_visible_location.sql     (extract lat/lon, filter nulls)
    ↓
int_stacked_location.sql            (GROUP BY lat/lon HAVING COUNT > 1)
    ↓
marts_acteur_stacked.sql            (JOIN acteurs with stacked locations)
    ↓
exposure_stats_acteur_stacked_history.sql  (incremental: daily snapshot with counts & rates)
```

## Best Practices

### Do's

- **Use base layer** - Clean data once in base, reuse everywhere
- **Test aggressively** - `not_null`, `unique`, `data_tests` on key columns
- **Document everything** - Column descriptions in `schema.yml`
- **Use incremental** - For history/snapshot tables (exposure layer)
- **Use tags** - Tag models by subject (`stats`, `acteurs`) and layer (`base`, `marts`)
- **Use `env_var` for sampling** - `DBT_SAMPLING=true` for faster dev cycles

### Don'ts

- **Don't skip base** - Source → marts is tech debt
- **Don't hardcode schemas** - Declare sources in `source_*.yml`
- **Don't repeat logic** - Extract to macros (`macros/table/`, `macros/field/`)
- **Don't test in prod** - Use sampling and dev targets
- **Don't forget `schema.yml`** - Every folder needs one for documentation and tests

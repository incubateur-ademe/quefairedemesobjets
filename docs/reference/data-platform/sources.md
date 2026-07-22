# Ingestion sources and enrichment reference data

Inventory of data sources ingested by the platform and external reference datasets cloned for enrichment.

> **See also**: [Consolidation flow](../architecture/data-flow.md), [Airflow](airflow.md), [dbt](dbt.md).

## Actor sources

All sources below are exposed as **individual Airflow DAGs** (manual trigger, schedule `None`) under `data-platform/dags/sources/dags/`.

| Category      | Airflow DAG    | Source / endpoint                                         | Stream                        |
| ------------- | -------------- | --------------------------------------------------------- | ----------------------------- |
| Eco-organisme | `eo-aliapur`   | ALIAPUR (`data.pointsapport.ademe.fr`)                    | Tyres                         |
| Eco-organisme | `eo-batribox`  | BATRIBOX (`data.ademe.fr`)                                | Batteries                     |
| Eco-organisme | `eo-citeo`     | CITEO                                                     | Packaging & paper             |
| Eco-organisme | `eo-corepile`  | COREPILE                                                  | Batteries                     |
| Eco-organisme | `eo-cyclevia`  | CYCLEVIA                                                  | Lubricants                    |
| Eco-organisme | `eo-ecodds`    | ECODDS                                                    | DIY & garden items, chemicals |
| Eco-organisme | `eo-ecologic`  | ECOLOGIC                                                  | ABJ, ASL, EEE                 |
| Eco-organisme | `eo-ecomaison` | ECOMAISON                                                 | ABJ, furniture, toys, PMCB    |
| Eco-organisme | `eo-ecopae`    | ECOPAE                                                    | Chemicals                     |
| Eco-organisme | `eo-ecosystem` | ECOSYSTEM                                                 | EEE                           |
| Eco-organisme | `eo-pyreo`     | PYREO                                                     | Chemicals                     |
| Eco-organisme | `eo-refashion` | REFASHION                                                 | Textiles, linens, shoes       |
| Eco-organisme | `eo-soren`     | SOREN                                                     | EEE                           |
| Eco-organisme | `eo-valdelia`  | VALDELIA                                                  | PMCB                          |
| Eco-organisme | `eo-ocab`      | OCAB                                                      | OCA / PMCB                    |
| Eco-organisme | `eo-ocad3e`    | OCAD3E (QualiRépar label)                                 | EEE                           |
| API           | `cma`          | CMA Réparacteurs (`apiopendata.artisanat.fr/reparacteur`) | `reparacteur` label           |
| API           | `pharmacies`   | Ordre National des Pharmaciens (`ordre.pharmacien.fr`)    | Medicines                     |
| ADEME         | `source_sinoe` | ADEME SINOE (`data.ademe.fr`)                             | Recycling centres             |
| Custom        | `source-s3`    | S3 bucket `lvao-data-source`                              | Ad-hoc Excel files            |

## Cloned enrichment reference data

External data cloned into the database via `clone_*` DAGs, then cross-referenced by dbt.

> Business workflow of clone DAGs and dbt normalization logic: [Clone — Enrichment reference data](clone-referentiels.md).

| Reference data            | Source                                          | Usage                                                                                              |
| ------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| BAN                       | `adresse.data.gouv.fr`                          | Actor geocoding (`adresses-france.csv.gz`, `lieux-dits-beta-france.csv.gz`)                        |
| Annuaire Entreprises (AE) | `object.files.data.gouv.fr`, `www.data.gouv.fr` | SIREN/SIRET validation, closed establishment detection                                             |
| La Poste                  | `datanova.laposte.fr`                           | Postal codes (`laposte-hexasmal`)                                                                  |
| Koumoul                   | `opendata.koumoul.com`                          | EPCI                                                                                               |
| INSEE                     | `www.insee.fr`                                  | Municipalities (`v_commune_2025.csv`)                                                              |
| Contours administratifs   | `etalab-datasets.geo.data.gouv.fr`              | GeoJSON for municipalities / departments / regions / EPCIs / associated & delegated municipalities |

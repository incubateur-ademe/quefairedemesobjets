# Sources d'ingestion et référentiels d'enrichissement

Inventaire des sources de données ingérées par la plateforme et des référentiels externes clonés pour l'enrichissement.

> **Voir aussi** : [Flux de consolidation](../architecture/data-flow.md), [Airflow](airflow.md), [dbt](dbt.md).

## Sources d'acteurs

Toutes les sources ci-dessous sont exposées comme des **DAGs Airflow individuels** (déclenchement manuel, schedule `None`) sous `data-platform/dags/sources/dags/`.

| Catégorie     | DAG Airflow    | Source / endpoint                                         | Filière                                            |
| ------------- | -------------- | --------------------------------------------------------- | -------------------------------------------------- |
| Eco-organisme | `eo-aliapur`   | ALIAPUR (`data.pointsapport.ademe.fr`)                    | PNEU                                               |
| Eco-organisme | `eo-batribox`  | BATRIBOX (`data.ademe.fr`)                                | Piles & accus                                      |
| Eco-organisme | `eo-citeo`     | CITEO                                                     | Emballages & papiers                               |
| Eco-organisme | `eo-corepile`  | COREPILE                                                  | Piles & accus                                      |
| Eco-organisme | `eo-cyclevia`  | CYCLEVIA                                                  | Lubrifiants                                        |
| Eco-organisme | `eo-ecodds`    | ECODDS                                                    | Articles de bricolage & jardin, Produits chimiques |
| Eco-organisme | `eo-ecologic`  | ECOLOGIC                                                  | ABJ, ASL, EEE                                      |
| Eco-organisme | `eo-ecomaison` | ECOMAISON                                                 | ABJ, Éléments d'ameublement, Jouets, PMCB          |
| Eco-organisme | `eo-ecopae`    | ECOPAE                                                    | Produits chimiques                                 |
| Eco-organisme | `eo-ecosystem` | ECOSYSTEM                                                 | EEE                                                |
| Eco-organisme | `eo-pyreo`     | PYREO                                                     | Produits chimiques                                 |
| Eco-organisme | `eo-refashion` | REFASHION                                                 | Textiles, linges, chaussures                       |
| Eco-organisme | `eo-soren`     | SOREN                                                     | EEE                                                |
| Eco-organisme | `eo-valdelia`  | VALDELIA                                                  | PMCB                                               |
| Eco-organisme | `eo-ocab`      | OCAB                                                      | OCA / PMCB                                         |
| Eco-organisme | `eo-ocad3e`    | OCAD3E (label QualiRépar)                                 | EEE                                                |
| API           | `cma`          | CMA Réparacteurs (`apiopendata.artisanat.fr/reparacteur`) | Label `reparacteur`                                |
| API           | `pharmacies`   | Ordre National des Pharmaciens (`ordre.pharmacien.fr`)    | Médicaments                                        |
| ADEME         | `source_sinoe` | ADEME SINOE (`data.ademe.fr`)                             | Déchèteries                                        |
| Custom        | `source-s3`    | Bucket S3 `lvao-data-source`                              | Fichiers Excel ad-hoc                              |

## Référentiels d'enrichissement clonés

Données externes clonées en base via les DAGs `clone_*` puis exploitées en croisement par dbt.

| Référentiel               | Source                                          | Usage                                                                          |
| ------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------ |
| BAN                       | `adresse.data.gouv.fr`                          | Géocodage acteurs (`adresses-france.csv.gz`, `lieux-dits-beta-france.csv.gz`)  |
| Annuaire Entreprises (AE) | `object.files.data.gouv.fr`, `www.data.gouv.fr` | Validation SIREN/SIRET, détection établissements fermés                        |
| La Poste                  | `datanova.laposte.fr`                           | Codes postaux (`laposte-hexasmal`)                                             |
| Koumoul                   | `opendata.koumoul.com`                          | EPCI                                                                           |
| INSEE                     | `www.insee.fr`                                  | Communes (`v_commune_2025.csv`)                                                |
| Contours administratifs   | `etalab-datasets.geo.data.gouv.fr`              | GeoJSON commune / département / région / EPCI / communes associées & déléguées |

# Doc archi

## flux de consolidation de données

```mermaid
flowchart
    direction RL
    subgraph source["Sources de données"]
        direction TB
        subgraph eco-organisme["🌱 Eco-organismes"]
            direction LR
            aliapur["Aliapur"]
            batribox["Batribox"]
            citeo["Citeo"]
            corepile["Corepile"]
            cyclevia["Cyclevia"]
            ecodds["EcoDDS"]
            ecologic["Ecologic"]
            ecomaison["Ecomaison"]
            ecopae["EcoPae"]
            ecosystem["Ecosystem"]
            ocab["OCAB"]
            ocad3e["OCAD3E"]
            pyreo["Pyreo"]
            refashion["Refashion"]
            soren["Soren"]
            valdelia["Valdelia"]
        end
        subgraph api["📦 API"]
            direction RL
            cma["CMA"]
            pharmacies["Pharmacies"]
        end
        subgraph ademe["💚 ADEME"]
            direction LR
            sinoe["SINOE"]
        end
        subgraph autre["📦 Custom"]
            direction LR
            s3["S3"]
        end
    end
    subgraph webapp["WebApp"]
        direction LR
        lacarte["🗺️ La carte"]
        assistant["❓ L'assistant"]
    end
    subgraph externe["Import de données enrichissement"]
        direction LR
        ban["Banque d'adresse national"]
        ae["Annuaire entreprise"]
        laposte["La poste"]
        koumoul["Koumoul"]
        insee["INSEE"]
        contours["Contours Administratifs"]
    end
    dataplateform["DataPlateform / Django backend"]
    contrib["Constribtion manuel / équipe QFDMOD"]
    backoffice["Back office"]
    data["Données consolidées"]
    opendata["⌗ Open-Data"]
    externe --> dataplateform
    contrib --> backoffice
    backoffice --> data
    dataplateform --> data
    source --> dataplateform
    data --> webapp
    data --> opendata
```

## Architecture de l'application

```mermaid
flowchart
    direction LR
    subgraph Scalingo["☁️ Scalingo"]
        webapp["🌐 Webapp Django"]
    end

    subgraph Scaleway["☁️ Scaleway"]
        direction TB
        subgraph CaaS["Container as a Service"]
            direction LR
            airflow_webserver["🖥️ Airflow Webserver"]
            airflow_scheduler["⏰ Airflow Scheduler"]
        end

        subgraph Databases["🗄️ Bases de données"]
            direction LR
            db_webapp[("DB Webapp\n(PostgreSQL)")]
            db_warehouse[("DB Warehouse\n(PostgreSQL)")]
            db_airflow[("DB Airflow\n(PostgreSQL)")]
            db_warehouse <--> |"postgres_fdw"|db_webapp
        end
    end

    %% Connexions Webapp
    webapp --> db_webapp
    webapp -.->|"lecture"| db_warehouse

    %% Connexions Airflow
    airflow_scheduler --> db_airflow
    airflow_scheduler --> |"Copy"| db_webapp
    airflow_webserver --> db_airflow
    airflow_scheduler -->|"ETL"| db_warehouse

    %% Communication interne Airflow
    airflow_scheduler <-.->|"état des tâches"| airflow_webserver
```

## Description des composants

### Scalingo

- **Webapp Django** : Application web principale exposée aux utilisateurs

### Scaleway

#### Container as a Service (CaaS)

- **Airflow Webserver** : Interface web pour monitorer et gérer les DAGs
- **Airflow Scheduler** : Orchestrateur qui planifie et exécute les tâches ETL

#### Bases de données

| Base de données | Usage                                                 |
| --------------- | ----------------------------------------------------- |
| DB Webapp       | Données applicatives (utilisateurs, acteurs, etc.)    |
| DB Warehouse    | Données transformées pour l'analyse et l'alimentation |
| DB Airflow      | Métadonnées Airflow (état des DAGs, logs, etc.)       |

## Activités du service QFDMOD

Via l'orchestrateur Airflow

- Ingestion des données des sources avec Airflow, tag : source
- Clone de tables d'enrichissement de données
- Enrichissement de données
- Calcul des statistuques
- Maintenance - Nettoyage logs / xcoms

Via la CI/CD (github)

- Tests automatiques
- Nettoyage des backups de DB
- Copies de la base de données WebApp de prod vers la preprod
- Création d'un echantillonage de la base de données pour créer des données de test
- Gestion des releases
-

Via le fournisseur de Cloud

- Backup des bases de données (tous les jours)

Via le backoffice

-

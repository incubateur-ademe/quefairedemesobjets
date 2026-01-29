# 📊 Plateforme de données

```{toctree}
:hidden:

ingestion-de-source.md
flux-dbt.md
flux-enrich.md
```

Ce projet contient l'environnement d'execution d'Airflow

Les fichiers qui concerne la plateforme data :

- `pyproject.toml` définition des dépendances dans la section [dependency-groups]
- `./dags` répertoire dans lequels sont stockés tous les dags executés sur le cluster Airflow
- `airflow-scheduler.Dockerfile` et `airflow-webserver.Dockerfile`, fichier de configuration docker executer dans tous les environnements
- `docker-compose.yml` orchestre les dockers en envronnemnt de développement
- `./dags/tests` répertoire qui contient les tests des dags

## Environnements

On distingue 3 environements:

- `development` : airflow tourne localement en utilisant l'orchestrateur `docker compose` (cf. [docker-compose.yml](../../../docker-compose.yml))
- `preprod` et `prod` : Airflow tourne sur Scaleway

## Mise à jour du scheduler et du webserver sur Scaleway

Airflow utilise l'offre CaaS (Container as a Service) de Scaleway, chaque environnement est déployé dans un `namespace`:

- lvao-preprod
- lvao-prod

Dans chaque environnement, 2 conteneurs sont déployés:

- lvao-airflow-scheduler : scheduler d'airflow, orchestre et execute les dags car l'option `LocalExecutor` est active
- lvao-airflow-webserver : interface d'airflow

Chaque environnement utilise sa propre base de données :

- lvao-preprod-airflow
- lvao-prod-airflow

et chaque environnement utilise son espace de stockage s3 :

- lvao-preprod-airflow
- lvao-prod-airflow

## Déploiement et configuration

### CI/CD

la platefome Data est déployée en preprod à chaque mise à jour de la branche `main` sur Github (cf. [cd.yml](../../../.github/workflows/cd.yml))

Et en production à chaque depot de tag de version (cf. [cd_prod.yml](../../../.github/workflows/cd.yml))

De la même manière que l'interface, cela permet de garder la cohérance entre l'application web et la plateforme data

### Configuration du cluster Airflow

#### Variable d'environnement du cluster Airflow

Les variables d'environnement sont déployés lors de l'exécution des recettes terraform.

Un exemple à adapter selon l'environnement est disponible sur le fichier [.env.templates](../../../dags/.env.template)

#### Gestion des logs

Pour que les logs du scheduler soient stockés sur S3, les instances Scaleway sont lancés avec les variables d'environnement:

```
AIRFLOW__LOGGING__REMOTE_LOGGING=true
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://qfdmo-airflow-logs
AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID=s3logs
AIRFLOW__LOGGING__ENCRYPT_S3_LOGS=false
```

`s3logs` est une connection configuré dans l'interface d'Airflow

Attention à ajouter le paramètre endpoint_url pour le stockage S3 de Scaleway

# Gestion des secrets

Stockage et utilisation des secrets selon la couche d'exécution.

> **Voir aussi** : [Services externes](../architecture/external-services.md), [Authentification](authentication.md), [Provisioning](../infrastructure/provisioning.md), [Rotating database passwords](../../how-to/infrastructure/rotate_db_passwords.md).

| Couche                  | Stockage                                                                      | Utilisation                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Webapp (Scalingo)       | Variables d'environnement Scalingo                                            | `DATABASE_URL`, `SENTRY_DSN`, `AWS_*`, `NOTION_TOKEN`, clés PostHog, etc.                                     |
| Airflow (Scaleway)      | `secret_environment_variables` de `scaleway_container.airflow_*` (Terragrunt) | DSN bases, `AIRFLOW__API_AUTH__JWT_SECRET`, identifiants S3, credentials webserver.                           |
| CI/CD                   | GitHub Environments `preprod` / `prod` (rule sur `main`)                      | Tokens Scaleway / Scalingo / Mattermost / S3, IDs containers, `DJANGO_SCALINGO_APP_NAME`, `HEALTHCHECK_URLS`. |
| OpenTofu                | Scaleway Secret Manager, un secret par stack : `/terraform/<env>/<stack>`     | `webapp_db_password`, `warehouse_db_password`, `airflow_db_password`, variables d'Airflow et de Metabase.     |
| Coffre (Vaultwarden)    | [vaultwarden.incubateur.net](https://vaultwarden.incubateur.net)              | Copie hors Scaleway des secrets des stacks, par environnement.                                                |
| Détection en pré-commit | `detect-secrets`                                                              | Empêche les commits accidentels de secrets.                                                                   |

Pour faire tourner les mots de passe des bases PostgreSQL (webapp, warehouse, Airflow), suivre [Rotating database passwords](../../how-to/infrastructure/rotate_db_passwords.md).

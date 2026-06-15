# Gestion des secrets

Stockage et utilisation des secrets selon la couche d'exécution.

> **Voir aussi** : [Services externes](../architecture/external-services.md), [Authentification](authentication.md), [Provisioning](../infrastructure/provisioning.md).

| Couche                  | Stockage                                                                                  | Utilisation                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Webapp (Scalingo)       | Variables d'environnement Scalingo                                                        | `DATABASE_URL`, `SENTRY_DSN`, `AWS_*`, `NOTION_TOKEN`, clés PostHog, etc.                                     |
| Airflow (Scaleway)      | `secret_environment_variables` de `scaleway_container.airflow_*` (Terragrunt)             | DSN bases, `AIRFLOW__API_AUTH__JWT_SECRET`, identifiants S3, credentials webserver.                           |
| CI/CD                   | GitHub Environments `preprod` / `prod` (rule sur `main`)                                  | Tokens Scaleway / Scalingo / Mattermost / S3, IDs containers, `DJANGO_SCALINGO_APP_NAME`, `HEALTHCHECK_URLS`. |
| OpenTofu                | `infrastructure/environments/<env>/terraform.tfvars` (non versionnés, `sensitive = true`) | `db_password`, `project_id`, `organization_id`.                                                               |
| Détection en pré-commit | `detect-secrets`                                                                          | Empêche les commits accidentels de secrets.                                                                   |

# Monitoring

Outils d'observabilité applicative et infrastructure.

> **Voir aussi** : [Sécurité — vue d'ensemble](../security/README.md) (CodeQL / GitGuardian / Dependabot / Dashlord), [Architecture applicative](../architecture/README.md), [CI/CD](ci-cd.md).

## Vue d'ensemble

| Outil                          | Périmètre                         | Détail                                                                                                                                                                                                                           |
| ------------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sentry**                     | Erreurs back-end + front-end      | `sentry-sdk` (`DjangoIntegration`, `LoggingIntegration`, `traces_sample_rate=0.01`) + `@sentry/browser`. [Projet beta.gouv](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/?project=115). |
| **PostHog EU**                 | Analytics produit + feature flags | A/B testing (`produit-carte-default-view-mobile`), HogQL pour `/api/stats`. Proxy `/ph/*` côté nginx Scalingo (first-party).                                                                                                     |
| **Matomo**                     | Statistiques d'audience           | `stats.beta.gouv.fr` via template tag `{% matomo %}`.                                                                                                                                                                            |
| **Scaleway Cockpit (Grafana)** | Métriques infra                   | Dashboards RDB PostgreSQL et containers (voir ci-dessous).                                                                                                                                                                       |
| **Mattermost**                 | Notifications                     | Canal `lvao-tour-de-controle` — début de déploiement, succès (avec URL), échec (avec lien logs), site down post-deploy.                                                                                                          |
| **Healthcheck post-deploy**    | Disponibilité                     | `HEALTHCHECK_URLS` vérifié après chaque déploiement webapp.                                                                                                                                                                      |

## Scaleway monitoring

Pour superviser les bases de données, Scaleway expose un [dashboard Grafana](https://6bef58ea-39e7-4fa5-8a55-dc3999fc62df.dashboard.cockpit.fr-par.scw.cloud/d/scw-rdb-postgresql-overview/rdb-postgresql-overview?orgId=1&var-region=fr-par&refresh=5m&var-metric_datasource=f8cd3b3c-ba53-4538-b6df-c44739a568e4&var-log_datasource=cd4bcf79-05e5-49c1-8d00-df1b7390a041&var-resource_name=lvao-prod-db&var-resource_id=All&var-instance=All).

Ce dashboard est accessible depuis l'onglet `Metrics` > `Open Grafana metrics dashboard` dans l'interface de gestion de chaque base.

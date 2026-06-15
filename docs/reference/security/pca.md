# Plan de continuité d'activité (PCA)

Mesures préventives et dispositifs permettant de **maintenir le service en fonctionnement** malgré les incidents (panne d'un composant, indisponibilité partielle d'un fournisseur, pic de charge, erreur humaine).

> **Voir aussi** : [Plan de reprise d'activité (PRA)](pra.md), [Sauvegardes](backups.md), [Revues régulières](reviews.md), [Provisioning](../infrastructure/provisioning.md), [Monitoring](../infrastructure/monitoring.md), [CI/CD](../infrastructure/ci-cd.md).

## Périmètre

| Service                                                                | Criticité | Disponibilité visée                                                      |
| ---------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------ |
| **Webapp publique** (carte, assistant, API REST, iframes intégrateurs) | Élevée    | Service de référence pour le grand public et les intégrateurs.           |
| **Django Admin / CMS Wagtail / `/data/`**                              | Moyenne   | Outils internes — indisponibilité tolérée le temps d'un incident.        |
| **Plateforme data (Airflow + dbt)**                                    | Moyenne   | Pipelines batchs — retard d'exécution acceptable, rattrapage par re-run. |
| **Documentation (GitHub Pages)**                                       | Faible    | Hors périmètre opérationnel critique.                                    |

## Haute disponibilité native

### Webapp Django (Scalingo `osc-fr1`)

| Mécanisme                                               | Détail                                                                                                                   |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Gunicorn multi-workers**                              | Plusieurs workers servent les requêtes en parallèle derrière nginx local (`bin/start`).                                  |
| **nginx Scalingo (cache)**                              | Couche de cache devant Gunicorn (`servers.conf.erb`) absorbe les pics de trafic anonymes. Bypass via cookie `logged_in`. |
| **WhiteNoise + `CompressedManifestStaticFilesStorage`** | Statiques servis directement par l'app, indépendants d'un CDN tiers.                                                     |
| **Cache applicatif en base**                            | `DatabaseCache` (table `qf_django_cache`) — pas de dépendance Redis à maintenir.                                         |
| **Scalabilité horizontale Scalingo**                    | Possibilité d'augmenter le nombre de containers `web` à la demande depuis l'interface Scalingo.                          |

### Bases de données (Scaleway RDB PostgreSQL 16)

| Mécanisme                  | Détail                                                                                                                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Offre RDB HA**           | Bases `lvao-{env}-webapp`, `lvao-{env}-warehouse`, `lvao-{env}-airflow` provisionnées en mode **Haute Disponibilité** (réplication synchrone + failover automatique géré par Scaleway). |
| **Point-in-time recovery** | Rétention PITR 24 h (granularité seconde) sur chaque base.                                                                                                                              |
| **`sslmode=require`**      | Chiffrement systématique des connexions clientes.                                                                                                                                       |

### Object Storage (Scaleway S3 `fr-par`)

| Mécanisme                 | Détail                                                                                                     |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Stockage objet managé** | Durabilité & disponibilité standards du service S3 Scaleway (multi-AZ).                                    |
| **Versioning**            | Activé sur `qfdmo-interface` — permet de récupérer une version antérieure d'un upload Django Admin.        |
| **Snapshots horodatés**   | `lvao-opendata` conserve l'historique des exports (`YYYYMMDDHHMMSS.csv`) en plus du `acteurs.csv` courant. |

### Airflow (Scaleway Container as a Service)

| Mécanisme               | Détail                                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Containers séparés**  | Webserver, scheduler et DAG processor déployés indépendamment — l'arrêt du webserver n'interrompt pas l'exécution des DAGs.              |
| **Re-run de DAG**       | Tout DAG en échec peut être relancé manuellement depuis l'UI sans perte (idempotence applicative à respecter par le développeur du DAG). |
| **Remote logs S3**      | `AIRFLOW__LOGGING__REMOTE_LOGGING=true` — les logs survivent au redéploiement des containers.                                            |
| **Cleanup automatique** | DAG `airflow_cleanup_db` purge quotidiennement la métadonnée Airflow pour éviter la saturation.                                          |

## Redondance opérationnelle

### Multi-environnements

| Environnement | Usage                                            | Bascule possible ?                                                                                                          |
| ------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| **Prod**      | Service public.                                  | —                                                                                                                           |
| **Preprod**   | Réplique fonctionnelle (sync hebdo des données). | Utilisable comme **environnement témoin** en cas d'incident sur la prod (lecture seule, validation d'une procédure de fix). |

### Sauvegardes

Le détail (PITR 24 h, dumps quotidiens 7 j, copies cross-region, versioning S3, état Terraform versionné) est centralisé dans [`backups.md`](backups.md).

### Infrastructure as Code

Toute l'infra Scaleway est décrite dans `infrastructure/` (OpenTofu + Terragrunt). L'état est stocké, versionné et chiffré dans le bucket `lvao-terraform-state`. **Conséquence PCA** : la totalité du socle peut être re-provisionnée à l'identique sans connaissance tribale.

## Prévention des incidents

### Avant déploiement (CI)

| Garde-fou                | Outil / workflow                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Tests automatisés**    | Unit / integration / E2E (Playwright) déclenchés sur chaque PR ([`ci-cd.md`](../infrastructure/ci-cd.md)). |
| **Migration checks**     | Vérification des migrations Django dans la CI avant merge.                                                 |
| **Linters & formatters** | Ruff, Black, Prettier, ESLint, `tofu fmt`, `terragrunt hclfmt`.                                            |
| **Scan sécurité**        | CodeQL, GitGuardian, Dependabot, `detect-secrets` en pre-commit ([`README.md`](README.md)).                |
| **Validation préprod**   | Déploiement explicite sur preprod possible depuis chaque PR avant merge.                                   |

### Pendant le déploiement (CD)

| Garde-fou                    | Détail                                                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Build & push registry**    | Images Airflow buildées et poussées sur `ns-qfdmo` avant déploiement des containers Scaleway.                               |
| **Healthcheck post-deploy**  | `HEALTHCHECK_URLS` interrogé après chaque déploiement webapp — déclenche une notification Mattermost si KO.                 |
| **Notifications temps réel** | Canal Mattermost `lvao-tour-de-controle` (début déploiement, succès avec URL, échec avec lien logs, site down post-deploy). |

### En production (monitoring)

| Garde-fou                      | Détail                                                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Sentry**                     | Détection en temps réel des erreurs back/front (`DjangoIntegration`, `@sentry/browser`).                   |
| **Scaleway Cockpit (Grafana)** | Métriques RDB PostgreSQL & containers Airflow.                                                             |
| **PostHog / Matomo**           | Surveillance indirecte de l'usage (chute de trafic = signal faible d'incident).                            |
| **Dashlord ADEME**             | Audit de sécurité externe continu ([dashlord.incubateur.ademe.fr](https://dashlord.incubateur.ademe.fr/)). |

## Stratégies de dégradation contrôlée

| Composant en panne            | Comportement attendu                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **API BAN / geo.api.gouv.fr** | Cache HTTP (1 h pour BAN, 30 j à 1 an pour EPCI) absorbe l'indisponibilité courte. L'autocomplete d'adresses dégrade silencieusement. |
| **Notion API**                | Le formulaire de contact échoue côté `post_save` — un retry/fallback peut être mis en place (à définir si nécessaire).                |
| **PostHog**                   | A/B testing et `/api/stats` indisponibles, mais le service principal (carte, assistant) reste fonctionnel.                            |
| **Matomo**                    | Aucune incidence fonctionnelle (analytics uniquement).                                                                                |
| **Sentry**                    | Aucune incidence fonctionnelle, mais perte temporaire de visibilité sur les erreurs.                                                  |
| **Scaleway Object Storage**   | Les images médias (uploads Django Admin) ne se chargent plus côté front, mais les pages restent servies.                              |
| **Airflow**                   | Les pipelines de données sont retardés — la webapp et l'API publique continuent de servir les données déjà consolidées.               |

## Rôles & responsabilités

| Rôle                     | Responsabilité PCA                                                                                          |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Équipe produit / dev** | Surveillance Mattermost / Sentry, déclenchement d'un rollback ou d'un re-run de DAG, communication interne. |
| **Scaleway**             | SLA infra (RDB HA, S3, Container Registry, CaaS).                                                           |
| **Scalingo**             | SLA hébergement webapp.                                                                                     |
| **GitHub**               | Disponibilité du code, des Actions CI/CD et de la documentation.                                            |

## Limites connues

- **Pas de VPC** : exposition publique des bases et containers, mitigée par `sslmode=require` et credentials forts ([`network.md`](network.md)).
- **Pas de Redis** : le cache applicatif est en base — saturation possible de `qf_django_cache` à surveiller via Cockpit.
- **Dépendance région unique** : prod et preprod sont toutes deux en région `fr-par` / `osc-fr1`. Les sauvegardes cross-region offrent une couverture en cas de sinistre régional (voir [PRA](pra.md)), mais pas de bascule chaud automatique.
- **RTO/RPO formels non contractualisés** : objectifs cibles documentés dans le [PRA](pra.md).

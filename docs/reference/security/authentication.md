# Authentification & autorisations

Mécanismes d'authentification et de gestion des autorisations sur les différentes surfaces de la plateforme.

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Sécurité réseau](network.md), [Gestion des secrets](secrets.md).

| Surface                            | Mécanisme                      | Détail                                                                                                                                                      |
| ---------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Site public**                    | Aucune                         | Accès anonyme à la carte, à l'assistant et à l'API REST `/api/`.                                                                                            |
| **API REST Django-Ninja**          | Aucune                         | Endpoints publics en lecture (`/api/qfdmo/*`, `/api/stats`).                                                                                                |
| **Django Admin** (`/admin/`)       | `django.contrib.auth` standard | `LOGIN_URL = "admin:login"`. Helper `core.utils.has_explicit_perm` pour bypasser le « superadmin a toutes les perms ». Pas d'OAuth / SSO / ProConnect.      |
| **Wagtail Admin** (`/cms/`)        | `django.contrib.auth`          | Permission custom `wagtailadmin.can_see_beta_search` créée par `qfdmd/management/commands/create_assistant_permissions.py`, contrôlée par `BetaMiddleware`. |
| **Back-office données** (`/data/`) | `LoginRequiredMixin`           | Workflow de validation des suggestions, vues Turbo-Stream.                                                                                                  |
| **Airflow** (`/`)                  | FAB (basic auth + session)     | Admin créé au bootstrap (`_AIRFLOW_WWW_USER_USERNAME/_PASSWORD/_EMAIL`, rôle `Admin`). JWT pour la communication inter-composants.                          |
| **Scaleway**                       | CLI + IAM                      | Provisioning OpenTofu/Terragrunt. Administration via le projet `longuevieauxobjets`.                                                                        |
| **Scalingo**                       | Clé SSH + token                | Déploiement via l'action GitHub `kolok/deploy-to-scalingo`.                                                                                                 |

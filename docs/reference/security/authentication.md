# Authentification & autorisations

Mécanismes d'authentification et de gestion des autorisations sur les différentes surfaces de la plateforme.

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Sécurité réseau](network.md), [Gestion des secrets](secrets.md), [Revues régulières](reviews.md).

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

## Procédure de revue des comptes Django Admin et Airflow

Réalisée chaque semestre (cf. [`reviews.md`](reviews.md) §Calendrier des revues) sur l'environnement **prod** (et **preprod** si des comptes y sont maintenus hors déploiement automatisé).

Les comptes Django Admin, Wagtail CMS et back-office `/data/` partagent le même modèle `User` de `django.contrib.auth` : une revue couvre les trois surfaces.

1. **Inventaire** : lister les utilisateurs

- via Django Admin → _Authentication and Authorization_ → _Users_ (`/admin/auth/user/`)
- via Airflow → _Sécurité_ → _Utilisateurs_

2. **Recoupement équipe** : comparer la liste avec les membres actifs de l'équipe et la [matrice d'accès](../../how-to/team/onboarding-offboarding.md) (rôles DEV → superuser, PO → droits limités, etc.).
3. **Comptes obsolètes** : désactiver (`is_active = False`) tout compte dont le titulaire a quitté l'équipe — ne pas supprimer pour conserver l'historique d'audit (cf. [offboarding](../../how-to/team/onboarding-offboarding.md)).
4. **Privilèges** : vérifier que `is_superuser` est réservé aux DEV ; retirer les droits superflus (groupes, permissions explicites) des comptes non superuser.
5. **Comptes techniques** : S'assurer que tous les comptes sont reliés à un utilisateur réel (pas de compte technique ou de test).
6. Consigner la revue dans [`reviews.md`](reviews.md) §Comptes Django Admin.

# Onboarding & offboarding des membres de l'équipe

Procédure d'**ouverture** (onboarding) et de **clôture** (offboarding) des accès des membres de l'équipe, en fonction de leur rôle.

> **Voir aussi** : [Prestataires](../../reference/security/providers.md), [Inventaire des actifs](../../reference/security/inventory.md), [Gestion des secrets](../../reference/security/secrets.md), [Authentification](../../reference/security/authentication.md).

> ⚠️ **Document à compléter** : la matrice ci-dessous est une proposition initiale, à ajuster selon les pratiques réelles de l'équipe.

## Rôles couverts

| Rôle                     | Code court | Description                                                                             |
| ------------------------ | ---------- | --------------------------------------------------------------------------------------- |
| **Data analyst**         | DA         | Exploration et restitution des données (warehouse, dashboards, qualité de la donnée).   |
| **Développeur**          | DEV        | Conception, code, déploiement, infrastructure, exploitation.                            |
| **Product Owner**        | PO         | Pilotage produit, priorisation, animation des rituels, gestion des contenus éditoriaux. |
| **Coach / Intrapreneur** | COACH      | Accompagnement de la startup d'État, posture transverse, sponsor côté ADEME.            |
| **Business Developer**   | BIZ        | Relations partenaires, acquisition d'intégrateurs, communication externe.               |

## Matrice des accès par rôle

Légende :

- **Admin** : droits d'administration (création/suppression de ressources, gestion des autres comptes).
- **Write** : lecture + modification du contenu / des configurations.
- **Read** : lecture seule.
- **—** : pas d'accès par défaut (à ouvrir à la demande si besoin justifié).

| Accès / Service                                                                                       | DA                    | DEV                    | PO                     | COACH     | BIZ                    |
| ----------------------------------------------------------------------------------------------------- | --------------------- | ---------------------- | ---------------------- | --------- | ---------------------- |
| **GitHub** — org `incubateur-ademe`, repo `quefairedemesobjets`                                       | Read                  | Write/Maintain         | Read                   | —         | —                      |
| **GitHub** — Environments `preprod` / `prod` (secrets CI)                                             | —                     | Admin                  | —                      | —         | —                      |
| **GitHub** — Discussions / Issues                                                                     | Read                  | Write                  | Write                  | Read      | Write                  |
| **Scalingo** — applications webapp (`preprod`, `prod`)                                                | —                     | Collaborator           | —                      | —         | —                      |
| **Scaleway** — projet `longuevieauxobjets` (IAM)                                                      | Read (Warehouse)      | Admin                  | —                      | —         | —                      |
| **DB Webapp** `lvao-{env}-webapp` (PostgreSQL)                                                        | —                     | Admin                  | —                      | —         | —                      |
| **DB Warehouse** `lvao-{env}-warehouse` (PostgreSQL)                                                  | Read                  | Admin                  | —                      | —         | —                      |
| **DB Airflow** `lvao-{env}-airflow` (PostgreSQL)                                                      | —                     | Admin                  | —                      | —         | —                      |
| **Django Admin** (`/admin/`)                                                                          | —                     | Superuser              | Write (limité)         | —         | —                      |
| **Wagtail CMS** (`/cms/`)                                                                             | —                     | Superuser              | Editor                 | —         | Editor (selon contenu) |
| **Back-office données** (`/data/`)                                                                    | Read                  | Write                  | Read                   | —         | —                      |
| **Airflow UI** (`webserver`)                                                                          | Read (Viewer)         | Admin                  | —                      | —         | —                      |
| **Scaleway Container Registry** `ns-qfdmo`                                                            | —                     | Push/Pull              | —                      | —         | —                      |
| **Scaleway Object Storage** (`qfdmo-interface`, `lvao-opendata`…)                                     | Read (opendata)       | Admin                  | —                      | —         | Read (opendata)        |
| **OpenTofu / Terragrunt** (`terraform.tfvars`, bucket `lvao-terraform-state`)                         | —                     | Admin                  | —                      | —         | —                      |
| **Sentry** (beta.gouv — projet `que-faire-de-mes-objets`)                                             | Read                  | Admin                  | Read                   | —         | —                      |
| **PostHog EU**                                                                                        | Read                  | Admin                  | Read                   | —         | Read                   |
| **Matomo** (`stats.beta.gouv.fr`)                                                                     | Read                  | Read                   | Read                   | Read      | Read                   |
| **Scaleway Cockpit (Grafana)**                                                                        | Read                  | Admin                  | —                      | —         | —                      |
| **Mattermost** — canal `lvao-tour-de-controle` (alertes deploy)                                       | Membre                | Membre                 | Membre                 | —         | —                      |
| **Mattermost** — canal équipe / produit                                                               | Membre                | Membre                 | Membre                 | Membre    | Membre                 |
| **Notion** — workspace équipe (specs, formulaire contact)                                             | Membre                | Membre                 | Admin                  | Membre    | Membre                 |
| **Tally.so** — formulaires hébergés                                                                   | —                     | Admin                  | Editor                 | —         | Editor                 |
| **Coffre de secrets** (variables sensibles, voir [`secrets.md`](../../reference/security/secrets.md)) | —                     | Accès complet          | —                      | —         | —                      |
| **Documentation** (GitHub Pages — publié via CI `publish-docs`)                                       | Read (édition via PR) | Write (édition via PR) | Write (édition via PR) | Read      | Read                   |
| **Dashlord ADEME** ([dashlord.incubateur.ademe.fr](https://dashlord.incubateur.ademe.fr/))            | Read                  | Read                   | Read                   | Read      | Read                   |
| **Outils internes ADEME** (intranet, accès bureaux, badges)                                           | À définir             | À définir              | À définir              | À définir | À définir              |

## Procédure d'onboarding

À réaliser par un **administrateur de la plateforme** (rôle DEV avec droits Admin sur les services concernés) **dès l'arrivée** du nouveau membre.

### 1. Identifier le rôle et les accès cibles

- [ ] Identifier le rôle du nouveau membre (DA / DEV / PO / COACH / BIZ).
- [ ] Identifier d'éventuels accès supplémentaires hors profil par défaut (mission spécifique).
- [ ] Récupérer les identifiants nécessaires : email professionnel, identifiant GitHub, identifiant Mattermost.

### 2. Créer les comptes selon la matrice

Pour chaque ligne de la matrice où le rôle a un accès `Read` / `Write` / `Admin` :

- [ ] **GitHub** : inviter l'utilisateur dans l'organisation `incubateur-ademe` et au repo `quefairedemesobjets` avec le niveau approprié.
- [ ] **Scalingo** (DEV uniquement) : ajouter comme collaborateur sur les apps `preprod` et `prod`.
- [ ] **Scaleway** : créer un compte IAM dans le projet `longuevieauxobjets` avec le rôle adapté.
- [ ] **Django Admin / Wagtail CMS / back-office `/data/`** : créer l'utilisateur via Django Admin et lui assigner les groupes/permissions adaptés.
- [ ] **Airflow** : créer l'utilisateur FAB avec le rôle adapté (`Viewer`, `User`, `Admin`).
- [ ] **Sentry** : inviter dans l'organisation beta.gouv (projet `que-faire-de-mes-objets`).
- [ ] **PostHog EU** : inviter dans le workspace.
- [ ] **Matomo** : ajouter dans `stats.beta.gouv.fr` (procédure beta.gouv).
- [ ] **Cockpit Scaleway (Grafana)** : ajouter au dashboard.
- [ ] **Mattermost** : inviter dans les canaux concernés.
- [ ] **Notion** : inviter dans le workspace, attribuer le rôle adapté.
- [ ] **Tally** : ajouter comme collaborateur si pertinent.
- [ ] **Coffre de secrets** (DEV uniquement) : partager les credentials nécessaires via le canal sécurisé en vigueur.
- [ ] **Dashlord** : pas de gestion individuelle (public).

### 3. Documenter & accompagner

- [ ] Communiquer le lien vers cette documentation : [docs.incubateur-ademe.github.io/quefairedemesobjets](https://incubateur-ademe.github.io/quefairedemesobjets/README.html).
- [ ] Pour les DEV : guider l'installation locale ([`installation.md`](../development/installation.md)) et la lecture des bonnes pratiques ([`secure_development.md`](../development/secure_development.md)).
- [ ] Présenter les rituels d'équipe et les canaux de communication.
- [ ] Assigner un référent / parrain (pair programming pour les DEV, shadow pour les autres rôles).

### 4. Confirmer

- [ ] Le nouveau membre confirme avoir accès à l'ensemble des services prévus.
- [ ] Tracer l'onboarding dans le registre interne (date, membre, rôle, référent).

## Procédure d'offboarding

À réaliser par un **administrateur de la plateforme** **dans les 48 h** suivant le départ effectif.

> ⚠️ **Priorité** : révoquer en premier les accès aux ressources critiques (GitHub, Scaleway, Scalingo, bases de données, coffre de secrets).

### 1. Inventorier les accès du membre sortant

- [ ] Récupérer la matrice du rôle dans la section ci-dessus pour disposer de la liste exhaustive.
- [ ] Identifier d'éventuels accès supplémentaires ouverts hors profil par défaut.

### 2. Révoquer les comptes

Pour chaque ligne de la matrice où le rôle avait un accès :

- [ ] **GitHub** : retirer de l'organisation `incubateur-ademe`. Vérifier qu'aucune branche / PR ouverte ne dépend exclusivement du membre.
- [ ] **GitHub Environments** : retirer des reviewers / approbateurs `preprod`, `prod`.
- [ ] **Scalingo** : retirer comme collaborateur.
- [ ] **Scaleway** : supprimer le compte IAM et révoquer les clés API actives.
- [ ] **Django Admin / Wagtail CMS / `/data/`** : désactiver l'utilisateur (`is_active = False`) — préférer la désactivation à la suppression pour conserver l'historique d'audit.
- [ ] **Airflow** : désactiver l'utilisateur FAB.
- [ ] **Sentry** : retirer du projet.
- [ ] **PostHog** : retirer du workspace.
- [ ] **Matomo** : retirer.
- [ ] **Cockpit Scaleway** : retirer.
- [ ] **Mattermost** : retirer des canaux internes (le canal `lvao-tour-de-controle` doit être nettoyé même si la personne reste sur l'instance).
- [ ] **Notion** : retirer du workspace, transférer la propriété des pages partagées.
- [ ] **Tally** : retirer.
- [ ] **Coffre de secrets** : retirer le membre.

### 3. Faire tourner les secrets exposés

Pour tout secret auquel le membre avait accès :

- [ ] **Rotation immédiate** des secrets qu'il avait pu manipuler en clair (selon procédure de [`secrets.md`](../../reference/security/secrets.md)) :
  - `DATABASE_URL`, `SENTRY_DSN`, clés API Scaleway / Scalingo, tokens Mattermost / Notion / PostHog…
  - Mettre à jour les variables Scalingo, Terragrunt (`secret_environment_variables` Airflow) et GitHub Environments.
  - Redéployer la webapp et les containers Airflow.
- [ ] Vérifier l'absence d'activité suspecte post-départ via Sentry / logs Scaleway / journaux GitHub.

### 4. Transférer les responsabilités

- [ ] Réattribuer les PR ouvertes, issues assignées, pages Notion / Wagtail dont le membre était auteur.
- [ ] Mettre à jour les éventuelles mentions du membre dans la documentation ou les fichiers `CODEOWNERS`.
- [ ] Documenter dans le registre interne (date de départ, accès révoqués, secrets renouvelés, point bloquant éventuel).

### 5. Confirmer

- [ ] Tous les accès listés dans la matrice du rôle sont effectivement révoqués.
- [ ] Les secrets exposés ont été rotés.
- [ ] Le registre interne est à jour.

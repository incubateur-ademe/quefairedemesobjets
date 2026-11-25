# Onboarding & offboarding des membres de l'équipe

Procédure d'**ouverture** (onboarding) et de **clôture** (offboarding) des accès des membres de l'équipe, en fonction de leur rôle.

> **Voir aussi** : [Prestataires](../../reference/security/providers.md), [Inventaire des actifs](../../reference/security/inventory.md), [Gestion des secrets](../../reference/security/secrets.md), [Authentification](../../reference/security/authentication.md), [Revues régulières](../../reference/security/reviews.md) §Comptes Django Admin.

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

| Accès / Service                                                                                       | DA                     | DEV                    | PO                     | COACH  | BIZ    |
| ----------------------------------------------------------------------------------------------------- | ---------------------- | ---------------------- | ---------------------- | ------ | ------ |
| **GitHub** — org `incubateur-ademe`, repo `quefairedemesobjets`                                       | Read                   | Write/Maintain         | Read                   | —      | —      |
| **GitHub** — Environments `preprod` / `prod` (secrets CI)                                             | —                      | Admin                  | —                      | —      | —      |
| **GitHub** — Discussions / Issues                                                                     | Write                  | Write                  | Write                  | Write  | Write  |
| **Scalingo** — applications webapp (`preprod`, `prod`)                                                | —                      | Collaborator           | —                      | —      | —      |
| **Scaleway** — projet `longuevieauxobjets` (IAM)                                                      | Read (Warehouse)       | Admin                  | —                      | —      | —      |
| **Django Admin** (`/admin/`)                                                                          | Superuser              | Superuser              | —                      | —      | —      |
| **Wagtail CMS** (`/cms/`)                                                                             | —                      | Superuser              | Editor                 | —      | Editor |
| **Airflow UI** (`webserver`)                                                                          | Admin                  | Admin                  | —                      | —      | —      |
| **Scaleway Container Registry** `ns-qfdmo`                                                            | —                      | Push/Pull              | —                      | —      | —      |
| **Scaleway Object Storage** (`qfdmo-interface`, `lvao-opendata`…)                                     | Read (opendata)        | Admin                  | —                      | —      | —      |
| **OpenTofu / Terragrunt** (Secret Manager `/terraform`, bucket `lvao-terraform-state`)                | —                      | Admin                  | —                      | —      | —      |
| **Sentry** (beta.gouv — projet `que-faire-de-mes-objets`)                                             | Read                   | Admin                  | Read                   | —      | —      |
| **PostHog EU**                                                                                        | Read                   | Admin                  | Read                   | —      | Read   |
| **Matomo** (`stats.beta.gouv.fr`)                                                                     | Read                   | Read                   | Read                   | Read   | Read   |
| **Scaleway Cockpit (Grafana)**                                                                        | Read                   | Admin                  | —                      | —      | —      |
| **Mattermost** — canal `lvao-tour-de-controle` (alertes deploy)                                       | Membre                 | Membre                 | Membre                 | —      | —      |
| **Mattermost** — canal équipe / produit                                                               | Membre                 | Membre                 | Membre                 | Membre | Membre |
| **Notion** — workspace équipe (specs, formulaire contact)                                             | Membre                 | Membre                 | Admin                  | Membre | Membre |
| **Tally.so** — formulaires hébergés                                                                   | —                      | Admin                  | Editor                 | —      | Editor |
| **Coffre de secrets** (variables sensibles, voir [`secrets.md`](../../reference/security/secrets.md)) | —                      | Accès complet          | —                      | —      | —      |
| **Documentation** (GitHub Pages — publié via CI `publish-docs`)                                       | Write (édition via PR) | Write (édition via PR) | Write (édition via PR) | Read   | Read   |
| **Dashlord ADEME** ([dashlord.incubateur.ademe.fr](https://dashlord.incubateur.ademe.fr/))            | Read                   | Read                   | Read                   | Read   | Read   |

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

À réaliser par un **administrateur de la plateforme**, dans les délais suivants à compter du départ effectif :

| Périmètre                                                                                                                                                                               | Délai                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Accès critiques** : GitHub (organisation et Environments), Scaleway, Scalingo, coffre de secrets (Vaultwarden), comptes superuser Django / Wagtail, Airflow, bases de données de prod | **Le jour du départ**       |
| **Autres accès** : Sentry, PostHog, Matomo, Cockpit, Mattermost, Notion, Tally, comptes Django / Wagtail non superuser                                                                  | **Sous 7 jours**            |
| **Secrets partagés** connus de la personne                                                                                                                                              | **Renouvelés sous 7 jours** |

Pour un départ planifié, les accès critiques sont retirés en fin de dernière journée. Pour un départ non planifié ou conflictuel, ils sont retirés dès que le départ est connu.

### 1. Inventorier les accès du membre sortant

- [ ] Récupérer la matrice du rôle dans la section ci-dessus pour disposer de la liste exhaustive.
- [ ] Identifier d'éventuels accès supplémentaires ouverts hors profil par défaut.

### 2. Révoquer les accès critiques (le jour du départ)

- [ ] **GitHub** : retirer de l'organisation `incubateur-ademe`. Vérifier qu'aucune branche / PR ouverte ne dépend exclusivement du membre.
- [ ] **GitHub Environments** : retirer des reviewers / approbateurs `preprod`, `prod`.
- [ ] **Scaleway** : supprimer le compte IAM et révoquer les clés API actives.
- [ ] **Scalingo** : retirer comme collaborateur.
- [ ] **Coffre de secrets (Vaultwarden)** : retirer le membre des collections partagées.
- [ ] **Django Admin / Wagtail CMS / `/data/`** (comptes superuser) : désactiver l'utilisateur (`is_active = False`) — préférer la désactivation à la suppression pour conserver l'historique d'audit.
- [ ] **Airflow** : désactiver l'utilisateur FAB.
- [ ] **Bases de données de prod** : supprimer tout accès direct nominatif (rôle PostgreSQL, adresse IP autorisée). Les identifiants partagés sont traités à l'étape 4.

### 3. Révoquer les autres accès (sous 7 jours)

- [ ] **Django Admin / Wagtail CMS / `/data/`** (comptes non superuser) : désactiver l'utilisateur (`is_active = False`).
- [ ] **Sentry** : retirer du projet.
- [ ] **PostHog** : retirer du workspace.
- [ ] **Matomo** : retirer.
- [ ] **Cockpit Scaleway** : retirer.
- [ ] **Mattermost** : retirer des canaux internes (le canal `lvao-tour-de-controle` doit être nettoyé même si la personne reste sur l'instance).
- [ ] **Notion** : retirer du workspace, transférer la propriété des pages partagées.
- [ ] **Tally** : retirer.

### 4. Renouveler les secrets partagés (sous 7 jours)

Pour tout secret partagé que le membre connaissait ou avait pu manipuler en clair, suivre la procédure de [Gestion des secrets](../../reference/security/secrets.md) :

- [ ] Renouveler les secrets : `DATABASE_URL` et mots de passe PostgreSQL ([Rotating database passwords](../infrastructure/rotate_db_passwords.md)), `SENTRY_DSN`, clés API Scaleway / Scalingo, tokens Mattermost / Notion / PostHog…
- [ ] Mettre à jour les variables Scalingo, les secrets des stacks dans Scaleway Secret Manager (`make -C infrastructure secrets-push`), les GitHub Environments et le coffre Vaultwarden.
- [ ] Redéployer la webapp et les containers Airflow.
- [ ] Vérifier l'absence d'activité suspecte post-départ via Sentry / logs Scaleway / journaux GitHub.

### 5. Transférer les responsabilités

- [ ] Réattribuer les PR ouvertes, issues assignées, pages Notion / Wagtail dont le membre était auteur.
- [ ] Mettre à jour les éventuelles mentions du membre dans la documentation ou les fichiers `CODEOWNERS`.
- [ ] Documenter dans le registre interne (date de départ, accès révoqués, secrets renouvelés, point bloquant éventuel).

### 6. Confirmer

- [ ] Les accès critiques ont été révoqués le jour du départ, les autres accès sous 7 jours.
- [ ] Les secrets partagés ont été renouvelés sous 7 jours.
- [ ] Le registre interne est à jour.

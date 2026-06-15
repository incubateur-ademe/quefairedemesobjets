# Bonnes pratiques de développement sécurisé

> **Public** : développeur·euses contribuant à `quefairedemesobjets`.
> **Objectif** : rappeler les règles à appliquer dans le quotidien du dev pour produire du code sûr, et garantir le respect des standards de qualité que nous suivons.

## Standards de référence

Nous nous engageons à respecter et à faire évoluer le produit en suivant les standards suivants. Toute Pull Request doit pouvoir être lue à l'aune de ces référentiels.

- **Standards de l'Incubateur ADEME** : [Les Standards de l'Incubateur de l'ADEME](https://app.notion.com/p/accelerateur-transition-ecologique-ademe/Les-Standards-de-l-Incubateur-de-l-ADEME-3276523d57d78008bd84f82041f51558) (rubriques _Qualité logicielle_ et _Sécurité_ notamment).
- **Standards beta.gouv.fr** : [https://standards.beta.gouv.fr/standards](https://standards.beta.gouv.fr/standards), en particulier :
  - _Sécurité_ : sensibilisation aux règles d'hygiène, identification et maîtrise des risques cyber, plan d'action d'homologation.
  - _Qualité logicielle_ : tests, observabilité, uniformité du code, documentation, déploiement continu.
  - _Vie privée_ : données de production cloisonnées à la production, documents légaux publiés.

Ces deux référentiels sont la grille de lecture utilisée en revue de code et lors des points de coordination produit.

## Règles à appliquer au quotidien

### 1. Ne jamais committer de secret

- Le hook **`detect-secrets`** est configuré dans [`.pre-commit-config.yaml`](../../../.pre-commit-config.yaml) et **doit** être installé en local (`uv run pre-commit install`).
- En cas de faux positif, mettre à jour `.secrets.baseline` (voir [troubleshooting](../troubleshooting.md)).
- GitGuardian inspecte également les commits poussés sur GitHub : un secret leaké doit immédiatement être **révoqué** chez le fournisseur concerné, puis remplacé. Le simple `git revert` n'efface pas l'historique.
- Pour le stockage et le cycle de vie des secrets, suivre [Gestion des secrets](../../reference/security/secrets.md).

### 2. Suivre les hooks de qualité avant chaque commit

Les contrôles `pre-commit` sont la première barrière de qualité ; ils ne doivent **jamais** être contournés (`--no-verify` interdit en dehors d'un cas exceptionnel justifié en PR).

| Outil                     | Rôle                                                |
| ------------------------- | --------------------------------------------------- |
| `ruff`                    | Lint Python (sécurité incluse via les règles `S*`). |
| `black`                   | Formatage Python.                                   |
| `djade`                   | Formatage des templates Django.                     |
| `prettier`                | Formatage JS/TS/CSS/MD.                             |
| `detect-secrets`          | Détection de secrets.                               |
| `check-yaml`              | Validation YAML.                                    |
| `check-added-large-files` | Empêche d'ajouter des fichiers > 600 KB.            |
| `tofu fmt`                | Formatage OpenTofu/Terragrunt.                      |

### 3. Gérer les dépendances avec précaution

- Ajouter une dépendance Python via `uv add <package>` depuis `webapp/` ou `data-platform/` (voir [Gestion de package](dependencies.md)).
- Pour npm, respecter le **cooldown de 7 jours** (`--before="$(date -v -7d +%Y-%m-%d)"`) pour limiter le risque de _supply chain attack_.
- Préférer des dépendances **maintenues, open source, à faible empreinte**.
- Les mises à jour automatiques sont gérées par **Dependabot** (hebdomadaire) : les PR Dependabot doivent être traitées (relues, mergées ou refusées explicitement).
- Avant d'introduire une nouvelle dépendance, vérifier qu'elle ne duplique pas une capacité déjà présente et qu'elle n'a pas de CVE ouverte sérieuse.

### 4. Écrire et exécuter les tests

- **Toute nouvelle fonctionnalité** ou **correction de bug** est accompagnée d'au moins un test (unitaire, intégration ou E2E selon le cas).
- Côté `webapp/` : `make unit-test`, `make integration-test`, et les E2E Playwright.
- Côté `data-platform/` : `make dags-test`.
- Les tests E2E couvrent les parcours critiques utilisateurs ; ils valident notamment les comportements anti-régression (CSRF, contrôle d'accès admin, etc.).

### 5. Sécuriser le code Django

- **Toujours utiliser l'ORM** ou des requêtes paramétrées : pas de SQL construit par concaténation de chaînes (risque d'injection).
- **Échapper les templates** : Django échappe par défaut ; ne **jamais** utiliser `|safe` ou `mark_safe` sur de l'entrée utilisateur non validée.
- **CSRF** activé sur toutes les vues mutables (POST/PUT/DELETE). Ne désactiver `csrf_exempt` que sur les endpoints publics en lecture documentés (cf. [API REST](../../reference/apis/README.md)).
- **Contrôle d'accès** sur les vues administratives : `LoginRequiredMixin`, `PermissionRequiredMixin`, ou `core.utils.has_explicit_perm` (cf. [Authentification](../../reference/security/authentication.md)).
- **`DEBUG = False` obligatoire** hors local ; ne jamais activer `DEBUG = True` en preprod/prod.
- Respecter `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_REFERRER_POLICY`, `SECURE_PROXY_SSL_HEADER` déjà définis dans `core/settings.py`.
- Tout nouveau header de sécurité (CSP, HSTS, etc.) ajouté ou modifié doit être documenté dans [Sécurité réseau](../../reference/security/network.md).

### 6. Sécuriser le code TypeScript / frontend

- Pas de `innerHTML` avec de l'entrée utilisateur ; préférer `textContent` ou les helpers du framework (Stimulus, Turbo).
- Valider toute donnée venant de `window.location`, `postMessage` ou d'un iframe parent avant utilisation.
- Vérifier l'origine des messages dans le contexte iframe (cf. [Sécurité réseau](../../reference/security/network.md) — section _Embeds iframe_).

### 7. Sécuriser l'infrastructure et la CI

- Les modifications d'infrastructure passent par **OpenTofu/Terragrunt** ; relire les _plans_ avant `apply`.
- Les variables sensibles vivent dans des `terraform.tfvars` **non versionnés** (`sensitive = true`).
- Les secrets CI/CD vivent dans les **GitHub Environments** `preprod`/`prod` (protection sur `main`).
- Ne **jamais** logguer un token, un secret ou une donnée personnelle en clair, ni dans Sentry, PostHog ou Matomo.

### 8. Ne pas utiliser les données de production hors production

- En local et en preprod, utiliser les bases de données dédiées et les jeux de fixtures (voir [Création d'une DB d'exemple](create_webapp_sample_db.md)).
- Les copies prod → preprod (`sync_databases.yml`) sont la **seule** voie autorisée et sont anonymisées/restreintes.
- Aucune donnée personnelle de production ne doit être copiée sur un poste de développeur en clair.

### 9. Revue de code (PR)

Chaque PR doit :

- être **petite et ciblée**, lisible en quelques minutes ;
- décrire l'intention (le _pourquoi_) et les impacts sécurité éventuels ;
- inclure les tests associés ;
- passer **toute la CI** (lint, format, tests, E2E) avant merge ;
- être relue par au moins **un·e autre développeur·euse**, qui s'assure du respect des points ci-dessus.

### 10. Observabilité et réaction

- Les erreurs runtime remontent dans [Sentry](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/) — y jeter un œil régulièrement, surtout après un déploiement.
- Dashlord ([https://dashlord.incubateur.ademe.fr/](https://dashlord.incubateur.ademe.fr/)) surveille la posture sécurité externe (headers, TLS, etc.) — toute régression doit être corrigée rapidement.
- Pour la chaîne d'observabilité complète : [Monitoring](../../reference/infrastructure/monitoring.md).

## Signaler ou réagir à une faille

- Une faille découverte dans le code ou en production se signale selon la procédure [SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md) (mail à `longuevieauxobjets@ademe.fr`).
- En cas de doute sur un comportement potentiellement sensible (donnée exposée, contrôle d'accès défaillant, dépendance vulnérable), **ne pas publier de PR ouverte** ; ouvrir un canal privé avec l'équipe d'abord.

## Pour aller plus loin

- [Référence — Sécurité](../../reference/security/README.md) (politique, monitoring, authentification, secrets, réseau, sauvegardes).
- [Référence — Code Guidelines](../../reference/coding/README.md).
- [Référence — CI/CD](../../reference/infrastructure/ci-cd.md).
- [Standards beta.gouv.fr](https://standards.beta.gouv.fr/standards).
- [Standards de l'Incubateur ADEME](https://app.notion.com/p/accelerateur-transition-ecologique-ademe/Les-Standards-de-l-Incubateur-de-l-ADEME-3276523d57d78008bd84f82041f51558).

# Maintien en conditions opérationnelles et de sécurité (MCO / MCS)

Détection des vulnérabilités, délais de correction selon la sévérité, répartition des rôles et suivi des fins de vie des composants.

> **Voir aussi** : [Revues régulières](reviews.md), [Gestion des incidents de sécurité](incidents.md), [Inventaire des actifs](inventory.md), [Plan de continuité d'activité (PCA)](pca.md), [CI/CD](../infrastructure/ci-cd.md), [Monitoring](../infrastructure/monitoring.md), [Dépendances](../../how-to/development/dependencies.md), [Déploiement](../../how-to/deployment/deployment.md).

## Détection des vulnérabilités

| Source                      | Périmètre                                                                       | Fréquence                                              | Effet                                                                                                                                                                                             |
| --------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dependabot**              | Dépendances `uv`, `npm`, GitHub Actions, modules et providers Terraform         | Hebdomadaire (mardi, 06:00 à 06:45 UTC)                | PR de mise à jour groupées. Délai de 7 jours (`cooldown`) avant de proposer une nouvelle version, contre les attaques de la chaîne d'approvisionnement. Configuration : `.github/dependabot.yml`. |
| **Trivy**                   | Images Docker webapp, Airflow (webserver, scheduler, DAG processor), ML         | À chaque build d'image, avant le push vers le registre | Bloque le push si l'image contient une vulnérabilité `CRITICAL` ou `HIGH` pour laquelle un correctif existe. Action : `.github/actions/trivy-scan-and-push/action.yml`.                           |
| **CodeQL**                  | Code du dépôt                                                                   | Configuration de l'incubateur                          | Alertes d'analyse statique dans l'onglet _Security_ de GitHub.                                                                                                                                    |
| **GitGuardian**             | Commits poussés sur GitHub                                                      | Configuration de l'incubateur                          | Alerte sur les secrets exposés (procédure dans [Gestion des secrets](secrets.md)).                                                                                                                |
| **Dashlord**, **Purplemet** | Services exposés de l'incubateur ADEME                                          | Continue                                               | Audit externe (en-têtes HTTP, TLS, versions exposées, vulnérabilités applicatives). L'incubateur transmet les constats à l'équipe.                                                                |
| **CERT-FR**                 | Avis et alertes de sécurité ([cert.ssi.gouv.fr](https://www.cert.ssi.gouv.fr/)) | À la publication                                       | Veille sur les composants listés en §Composants et fins de vie (Python, Django, PostgreSQL, Node.js, Airflow, nginx).                                                                             |

### Exceptions Trivy

Une vulnérabilité sans correctif applicable dans l'immédiat peut être ignorée dans `.trivyignore`, à la racine du dépôt :

- une ligne par CVE, avec une date d'expiration `exp:AAAA-MM-JJ` ;
- un commentaire au-dessus qui indique le composant touché et la condition de retrait ;
- à l'expiration, le scan bloque de nouveau le push : l'exception est retirée ou renouvelée en connaissance de cause.

## Tri

À la réception d'une alerte (PR Dependabot, échec Trivy, alerte CodeQL, signalement de l'incubateur, avis CERT-FR), un DEV de l'équipe :

1. Vérifie que la version vulnérable est réellement utilisée (`uv.lock`, `package-lock.json`, image concernée).
2. Évalue l'exposition : composant accessible depuis internet (webapp, API, gateway nginx) ou interne (Airflow, outils de build).
3. Recherche une exploitation active (alerte CERT-FR, catalogue [KEV de la CISA](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)).
4. Fixe la sévérité selon le tableau ci-dessous et le délai qui en découle.
5. Si la vulnérabilité est exploitée, ou laisse craindre une compromission, ouvre la [procédure d'incident](incidents.md).

## Délais de correction

| Sévérité     | Critère                                                                           | Délai de correction                               |
| ------------ | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Critique** | CVSS ≥ 9, exploitée activement ou touchant un composant exposé sur internet       | ≤ 72 h                                            |
| **Haute**    | CVSS 7 à 8,9, ou critique sur un composant non exposé et sans exploitation connue | ≤ 7 jours                                         |
| **Moyenne**  | CVSS 4 à 6,9                                                                      | ≤ 30 jours                                        |
| **Basse**    | CVSS < 4                                                                          | Prochaine mise à jour courante (cycle Dependabot) |

Le délai court à partir de la publication du correctif, ou de la détection si elle est postérieure. Pour une vulnérabilité critique ou haute, la mise à jour est faite à la main sans attendre la PR Dependabot ni le délai de 7 jours.

Si le délai ne peut pas être tenu (pas de correctif, régression bloquante) :

- appliquer une mesure de contournement : désactiver la fonctionnalité, filtrer la requête au niveau de nginx, restreindre l'accès ;
- documenter l'exception (entrée `.trivyignore` datée, ou alerte Dependabot ignorée avec un commentaire) ;
- fixer une date de réexamen.

## Qui fait quoi

| Acteur                         | Rôle                                                                                                                                                                                                                                             |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Équipe de la startup (DEV)** | Tri, mise à jour des dépendances ou des images, passage de la CI (tests unitaires, intégration, e2e), déploiement en preprod puis en prod, retour arrière en cas de régression ([Déploiement](../../how-to/deployment/deployment.md) §Rollback). |
| **Incubateur ADEME**           | Veille via ses outils (CodeQL, GitGuardian, Dashlord, Purplemet), information de l'équipe, suivi de la correction jusqu'à sa clôture.                                                                                                            |
| **Hébergeurs**                 | Maintien des services managés : Scaleway (RDB PostgreSQL, Serverless Containers, Object Storage), Scalingo (stack et buildpacks de la webapp). Voir [Prestataires](providers.md).                                                                |

## Composants et fins de vie

Versions relevées dans le code au 2026-11-25. Dates de fin de support issues de [endoflife.date](https://endoflife.date).

| Composant              | Version en usage                                  | Source dans le dépôt                               | Fin de support                                                    | Statut                      |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------- | --------------------------- |
| **Python**             | 3.12                                              | `.python-version`, `pyproject.toml`, images Docker | 2028-10-31 (correctifs de sécurité uniquement)                    | Supporté                    |
| **Django**             | 6.1.1                                             | `webapp/pyproject.toml`, `uv.lock`                 | 2027-12-31                                                        | Supporté                    |
| **Wagtail**            | 7.4.3 (LTS)                                       | `webapp/pyproject.toml`, `uv.lock`                 | 2027-11-02                                                        | Supporté                    |
| **PostgreSQL**         | 16 (Scaleway RDB)                                 | `infrastructure/modules/database/main.tf`          | 2028-11-09                                                        | Supporté                    |
| **Node.js** (CI)       | 20.19.0                                           | `.tool-versions`                                   | 2026-04-30                                                        | **Fin de support dépassée** |
| **Node.js** (image)    | 24                                                | `webapp/Dockerfile` (étape de build des assets)    | 2028-04-30                                                        | Supporté                    |
| **Node.js** (Scalingo) | Choisie par le buildpack (pas de champ `engines`) | `.buildpacks`                                      | À vérifier                                                        | À vérifier                  |
| **Apache Airflow**     | 3.3.1                                             | `data-platform/pyproject.toml`                     | 2026-11-07 (seule la dernière version mineure est maintenue)      | **Fin de support dépassée** |
| **Debian** (images)    | 12 « Bookworm »                                   | `webapp/Dockerfile` (`python:3.12-slim-bookworm`)  | Sécurité Debian jusqu'au 2026-07-11, puis LTS jusqu'au 2028-06-30 | En LTS                      |
| **nginx** (gateway)    | 1.31.9                                            | `nginx/nginx.Dockerfile` (`nginx:1.31.9-alpine`)   | Branche maintenue (pas de date de fin publiée)                    | Supporté                    |
| **nginx** (Scalingo)   | Fournie par le buildpack                          | `.buildpacks`                                      | À vérifier                                                        | À vérifier                  |

Les tags flottants d'images de base (`ruby:alpine`, `nginx:alpine`) sont traités dans un changement séparé.

Ce tableau est revu à chaque montée de version majeure et lors de la revue annuelle de l'[inventaire des actifs](inventory.md) ([Revues régulières](reviews.md)). Une montée de version est planifiée au moins trois mois avant la fin de support d'un composant.

## Limites connues

- L'image du gateway nginx (`nginx/nginx.Dockerfile`) n'est pas scannée par Trivy à son build.
- Node.js 20 (CI) et Airflow 3.3 ont dépassé leur fin de support : montées de version à planifier.
- Les versions de Node.js et de nginx utilisées sur Scalingo dépendent des buildpacks et ne sont pas fixées dans le dépôt.

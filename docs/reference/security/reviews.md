# Revues régulières

Calendrier et journal des revues récurrentes effectuées sur le périmètre sécurité de la plateforme.

> **Voir aussi** : [Inventaire des actifs](inventory.md), [Prestataires](providers.md), [PCA](pca.md), [PRA](pra.md), [Sauvegardes](backups.md).

## Principe

Plusieurs éléments du périmètre sécurité & conformité doivent être **revus à intervalles réguliers** pour rester pertinents :

- L'**inventaire des actifs** : pour refléter l'état réel du système d'information.
- Les **plans de continuité (PCA)** et **de reprise d'activité (PRA)** : pour vérifier que les procédures décrites restent applicables et que les RTO/RPO restent atteignables.
- Les **tests de restauration** (PITR, dumps, S3) : pour s'assurer que les sauvegardes sont réellement exploitables.
- L'**accessibilité numérique (RGAA)** : pour respecter l'obligation légale de conformité au Référentiel Général d'Amélioration de l'Accessibilité (audit, déclaration, schéma pluriannuel).
- Les **exigences de sécurité des prestataires** : pour vérifier le maintien des SLA, certifications (ISO 27001, HDS, SecNumCloud…) et DPA RGPD des fournisseurs critiques.
- Les **comptes Django Admin** (`/admin/`) et les **comptes Aiflow** : pour s'assurer que seuls les membres actifs de l'équipe disposent des droits attendus (staff, superuser, groupes/permissions).

Ce document centralise :

1. Le **calendrier** des revues planifiées.
2. Le **journal historique** de chaque revue effectuée.

> Les procédures détaillées (étapes à effectuer lors d'une revue) restent décrites dans les documents de référence (`inventory.md`, `pca.md`, `pra.md`). Ce document est le **registre opérationnel**.

## Calendrier des revues

| Revue                                                         | Fréquence cible            | Procédure                                                                                                                                                                                                                        | Dernière revue | Prochaine échéance |
| ------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------ |
| **Inventaire des actifs**                                     | Annuelle (ou changement)   | [`inventory.md`](inventory.md)                                                                                                                                                                                                   | 2026-06-11     | 2027-06-11         |
| **Revue documentaire PCA**                                    | Annuelle                   | [`pca.md`](pca.md)                                                                                                                                                                                                               | —              | 2027-06-11         |
| **Revue documentaire PRA**                                    | Annuelle                   | [`pra.md`](pra.md)                                                                                                                                                                                                               | —              | 2027-06-11         |
| **Test restauration PITR DB Webapp**                          | Trimestrielle              | [`pra.md`](pra.md) §Tests                                                                                                                                                                                                        | —              | 2026-09-11         |
| **Test restauration depuis dump**                             | Semestrielle               | [`pra.md`](pra.md) §Tests                                                                                                                                                                                                        | —              | 2026-12-11         |
| **Test récupération objet S3 versionné**                      | Annuelle                   | [`pra.md`](pra.md) §Tests                                                                                                                                                                                                        | —              | 2027-06-11         |
| **Test bascule cross-region** (à planifier)                   | À définir                  | [`pra.md`](pra.md) §Scénario 5                                                                                                                                                                                                   | —              | À planifier        |
| **Audit RGAA complet**                                        | Triennale                  | Audit externe ou interne sur l'échantillon RGAA en vigueur.                                                                                                                                                                      | —              | À planifier        |
| **Mise à jour de la déclaration d'accessibilité**             | Annuelle                   | CMS Wagtail (page liée via `CARTE.DECLARATION_ACCESSIBILITE_PAGE_ID`).                                                                                                                                                           | —              | À planifier        |
| **Schéma pluriannuel d'accessibilité + plan d'action annuel** | Annuelle                   | Document publié sur le site.                                                                                                                                                                                                     | —              | À planifier        |
| **Scan automatisé d'accessibilité (axe-core)**                | À chaque PR + à la demande | `make a11y` (Playwright + axe-core, tags `wcag2a/aa`, `wcag21a/aa`) — voir [`webapp/e2e_tests/accessibility.spec.ts`](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/webapp/e2e_tests/accessibility.spec.ts). | —              | Continu            |
| **Exigences de sécurité des prestataires**                    | Annuelle                   | [`providers.md`](providers.md) §Procédure de revue annuelle                                                                                                                                                                      | —              | 2027-06-11         |
| **Comptes Django Admin** (`/admin/`)                          | Semestrielle               | [`authentication.md`](authentication.md) §Procédure de revue des comptes Django Admin et Airflow                                                                                                                                 | —              | 2026-12-11         |
| **Comptes Airflow**                                           | Semestrielle               | [`authentication.md`](authentication.md) §Procédure de revue des comptes Django Admin et Airflow                                                                                                                                 | —              | 2026-12-11         |

## Journaux

### Inventaire des actifs

À chaque revue : vérifier l'exhaustivité de l'[inventaire](inventory.md), confirmer la priorité (1 ou 2) et la sensibilité de chaque actif, mettre à jour les liens vers la documentation associée, puis compléter le tableau ci-dessous.

| Date       | Auteur     | Périmètre vérifié                                                 | Observations          |
| ---------- | ---------- | ----------------------------------------------------------------- | --------------------- |
| 2026-06-11 | Équipe dev | Inventaire initial (Priorité 1 + Priorité 2 + actifs transverses) | Création du document. |

### Revue documentaire PCA

À chaque revue : relire le [PCA](pca.md), confirmer la pertinence des mécanismes HA listés, mettre à jour les stratégies de dégradation contrôlée selon les nouveaux services intégrés, ajuster les limites connues.

| Date | Auteur | Périmètre vérifié | Observations |
| ---- | ------ | ----------------- | ------------ |
| —    | —      | —                 | —            |

### Revue documentaire PRA

À chaque revue : relire le [PRA](pra.md), confirmer les RTO/RPO cibles, mettre à jour les scénarios suite aux changements d'infra, intégrer les retours d'expérience des incidents survenus dans la période.

| Date | Auteur | Périmètre vérifié | Observations |
| ---- | ------ | ----------------- | ------------ |
| —    | —      | —                 | —            |

### Tests de restauration

À chaque test : exécuter la procédure correspondante (cf. [`pra.md`](pra.md) §Tests & maintenance), consigner le résultat ci-dessous, et corriger immédiatement toute anomalie détectée.

| Date | Auteur | Type de test | Résultat | Observations |
| ---- | ------ | ------------ | -------- | ------------ |
| —    | —      | —            | —        | —            |

### Accessibilité numérique (RGAA)

Le projet est soumis à l'obligation légale d'accessibilité numérique (RGAA, aligné sur WCAG 2.1 AA). Trois niveaux de contrôle se complètent :

- **Scan automatisé continu** : `make a11y` exécute Playwright + axe-core avec les tags `wcag2a/aa` et `wcag21a/aa` sur les pages principales et iframes (formulaire, carte, assistant). Voir [`webapp/e2e_tests/accessibility.spec.ts`](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/webapp/e2e_tests/accessibility.spec.ts).
- **Audit RGAA complet** (idéalement triennal) : passage sur l'échantillon RGAA en vigueur, externe de préférence. Produit un **taux de conformité** publié dans la déclaration.
- **Mise à jour annuelle** de la déclaration d'accessibilité et du schéma pluriannuel + plan d'action annuel.

À chaque action effectuée, consigner ci-dessous (date, auteur, type, conformité atteinte / version RGAA, lien vers le rapport ou la déclaration publiée).

| Date | Auteur | Type d'action                                        | Résultat / Taux | Observations |
| ---- | ------ | ---------------------------------------------------- | --------------- | ------------ |
| —    | —      | Audit RGAA / Déclaration / Schéma pluriannuel / Scan | —               | —            |

### Exigences de sécurité des prestataires

À chaque revue : appliquer la procédure décrite dans [`providers.md`](providers.md) §Procédure de revue annuelle (vérification inventaire, certifications, SLA, DPA RGPD, alternatives) puis consigner ci-dessous.

| Date | Auteur | Prestataires revus                                                                                            | Observations |
| ---- | ------ | ------------------------------------------------------------------------------------------------------------- | ------------ |
| —    | —      | Hébergeurs critiques (Scaleway, Scalingo) + services applicatifs (GitHub, PostHog, Notion, Tally, Cloudflare) | —            |

### Comptes Django Admin

À chaque revue : appliquer la procédure décrite dans [`authentication.md`](authentication.md) §Procédure de revue des comptes Django Admin et airflow (inventaire des utilisateurs, recoupement avec la matrice d'onboarding/offboarding, ajustement des droits) puis consigner ci-dessous.

| Date       | Auteur         | Environnement | Comptes revus | Observations |
| ---------- | -------------- | ------------- | ------------- | ------------ |
| 18/06/2026 | Nicolas Oudard | prod          | tous          | —            |
| —          | —              | prod          | —             | —            |

### Comptes Airflow

À chaque revue : appliquer la procédure décrite dans [`authentication.md`](authentication.md) §Procédure de revue des comptes Django Admin et Airflow (inventaire des utilisateurs, recoupement avec la matrice d'onboarding/offboarding, ajustement des droits) puis consigner ci-dessous.

| Date       | Auteur         | Environnement | Comptes revus | Observations |
| ---------- | -------------- | ------------- | ------------- | ------------ |
| 18/06/2026 | Nicolas Oudard | prod          | tous          | —            |
| —          | —              | prod          | —             | —            |

## Ajouter une nouvelle revue récurrente

Pour intégrer une nouvelle action récurrente (ex. audit RGPD, revue des accès, rotation des secrets…) :

1. Ajouter une ligne dans le **calendrier des revues** ci-dessus (fréquence, procédure de référence, prochaine échéance).
2. Créer une sous-section dédiée dans **Journaux** avec un tableau adapté.
3. Renvoyer depuis le document de référence concerné vers ce fichier pour le suivi historique.

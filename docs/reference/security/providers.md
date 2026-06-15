# Prestataires & exigences de sécurité

Identification des prestataires critiques de la plateforme, de leurs engagements de niveau de service (SLA) et de leurs certifications de sécurité.

> **Voir aussi** : [Inventaire des actifs](inventory.md), [Provisioning](../infrastructure/provisioning.md), [Services externes](../architecture/external-services.md), [Revues régulières](reviews.md).

## Principe

Chaque prestataire utilisé par la plateforme est qualifié selon trois axes :

- **Criticité fonctionnelle** : impact d'une indisponibilité sur le service rendu (Élevée / Moyenne / Faible).
- **SLA contractuel** : engagement de disponibilité publié par le prestataire.
- **Conformité & certifications** : certifications de sécurité reconnues (ISO 27001, HDS, SecNumCloud, SOC 2…) et engagement RGPD (DPA).

Cette qualification est **revue annuellement** ([`reviews.md`](reviews.md)) pour tenir compte des évolutions (nouvelles certifications, changements de SLA, contentieux, migrations).

## Hébergeurs critiques (infrastructure)

### Scaleway

| Aspect              | Détail                                                                                                                                                                                  |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Périmètre**       | Bases RDB PostgreSQL HA (`lvao-{env}-webapp`, `-warehouse`, `-airflow`), Serverless Containers Airflow, Container Registry `ns-qfdmo`, Object Storage (5 buckets), tfstate OpenTofu.    |
| **Région utilisée** | `fr-par` (Paris) — non SecNumCloud à ce jour.                                                                                                                                           |
| **Criticité**       | **Élevée** — porte les données métier et la plateforme data.                                                                                                                            |
| **SLA contractuel** | Voir [SLA officiel par produit](https://www.scaleway.com/en/sla/) (RDB HA, Object Storage 99,99 % de disponibilité, Serverless Containers).                                             |
| **Certifications**  | **ISO/IEC 27001:2022**, **HDS** (Hébergeur de Données de Santé, depuis juillet 2024). **SecNumCloud 3.2** : qualification en cours (J0 obtenu en janvier 2025) — non acquise à ce jour. |
| **RGPD / DPA**      | DPA disponible. Hébergement et opérateur français (Iliad). Pas d'exposition CLOUD Act pour les régions EU.                                                                              |
| **Trust Center**    | [security.scaleway.com](https://security.scaleway.com/) (audits, rapports, politiques).                                                                                                 |
| **Page sécurité**   | [scaleway.com/en/security-and-resilience](https://www.scaleway.com/en/security-and-resilience/)                                                                                         |
| **Status page**     | [status.scaleway.com](https://status.scaleway.com/)                                                                                                                                     |

### Scalingo

| Aspect                       | Détail                                                                                                                                                                                                                           |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Périmètre**                | Webapp Django (gunicorn + nginx + WhiteNoise), routage public, déploiement continu via `kolok/deploy-to-scalingo`.                                                                                                               |
| **Région utilisée**          | `osc-fr1` (Outscale, France) — non SecNumCloud. Une région `osc-secnum-fr1` SecNumCloud 3.2 existe chez Scalingo mais n'est pas utilisée à ce jour par le projet.                                                                |
| **Criticité**                | **Élevée** — porte la webapp publique (carte, assistant, API, iframes).                                                                                                                                                          |
| **SLA contractuel**          | Voir [SLA officiel](https://scalingo.com/sla) (varie selon le plan).                                                                                                                                                             |
| **Certifications**           | **ISO/IEC 27001:2022** (depuis 2022), **HDS** (certificat n°38436 valide jusqu'à septembre 2028). Pas de qualification SecNumCloud du PaaS (en cours), mais accès possible à un IaaS SecNumCloud via la région `osc-secnum-fr1`. |
| **RGPD / DPA**               | DPA disponible. Hébergement souverain France (Outscale 3DS).                                                                                                                                                                     |
| **Documentation compliance** | [doc.scalingo.com/security/overview/compliance](https://doc.scalingo.com/security/overview/compliance)                                                                                                                           |
| **Page sécurité**            | [scalingo.com/security](https://scalingo.com/security)                                                                                                                                                                           |
| **Status page**              | [status.scalingo.com](https://scalingostatus.com/)                                                                                                                                                                               |

## Services applicatifs critiques

| Prestataire               | Périmètre                                                                     | Criticité | SLA / Sécurité                                                                                                                                                                    |
| ------------------------- | ----------------------------------------------------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GitHub**                | Code source, Actions CI/CD, déploiement, documentation (GitHub Pages).        | Élevée    | SOC 1/2 Type 2, ISO/IEC 27001, ISO 27017/27018. [SLA Online Services](https://github.com/customer-terms/github-online-services-sla), [Trust Center](https://github.com/security). |
| **PostHog EU**            | Analytics produit, A/B testing, HogQL pour `/api/stats`. Proxy nginx `/ph/*`. | Moyenne   | SOC 2 Type 2, ISO 27001, RGPD. [Security overview](https://posthog.com/handbook/company/security). Hébergement UE (Allemagne).                                                    |
| **Notion API**            | Réception du formulaire de contact (`FormSubmission`).                        | Faible    | SOC 2 Type 2. [Notion security](https://www.notion.so/security).                                                                                                                  |
| **Tally.so**              | Formulaires hébergés (feedback, suggestions, contact, assistant survey).      | Faible    | RGPD compliant, hébergement UE. [Data & privacy](https://tally.so/help/data-privacy).                                                                                             |
| **Cloudflare CDN**        | Sert `iframeResizer.contentWindow.js` aux pages intégratrices.                | Faible    | SOC 2 Type 2, ISO 27001, PCI DSS. [Trust Hub](https://www.cloudflare.com/trust-hub/).                                                                                             |
| **BAN / geo.api.gouv.fr** | Géocodage adresses + EPCI (API publiques État).                               | Faible    | Service public DINUM — pas de SLA contractuel, mitigé par cache HTTP (1 h à 1 an).                                                                                                |

## Services opérés par beta.gouv.fr / DINUM

Ces services sont **opérés par l'incubateur beta.gouv.fr (ADEME / DINUM)** et non par un prestataire externe direct. Ils suivent les politiques de sécurité de l'incubateur.

| Service              | Périmètre                                                     | Référence                                                                                                                   |
| -------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Sentry beta.gouv** | Monitoring d'erreurs back + front.                            | [sentry.incubateur.net](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/?project=115) |
| **Matomo beta.gouv** | Statistiques d'audience.                                      | `stats.beta.gouv.fr`                                                                                                        |
| **Mattermost ADEME** | Notifications de déploiement (canal `lvao-tour-de-controle`). | Plateforme interne ADEME.                                                                                                   |
| **Dashlord ADEME**   | Audit sécurité externe continu.                               | [dashlord.incubateur.ademe.fr](https://dashlord.incubateur.ademe.fr/)                                                       |

## Sensibilité des données hébergées

- **Aucune donnée de santé** n'est traitée par la plateforme : la certification HDS de Scaleway et Scalingo n'est pas un prérequis pour ce projet, mais constitue un signal positif de maturité sécurité.
- **Pas de données sensibles au sens RGPD** (origine raciale, opinions, santé, etc.) — la plateforme manipule essentiellement des données ouvertes (acteurs, propositions de service) et des comptes administrateurs internes.
- **Données personnelles limitées** : comptes Django/Wagtail (admins), formulaires de contact (transmis à Notion / Tally), analytics anonymisés (PostHog / Matomo).

À ce titre, le périmètre actuel **ne justifie pas le passage à des prestataires SecNumCloud**, mais cette possibilité reste ouverte (région `osc-secnum-fr1` chez Scalingo, qualification SecNumCloud en cours chez Scaleway).

## Procédure de revue annuelle

Réalisée chaque année (cf. [`reviews.md`](reviews.md) §Calendrier des revues) :

1. **Inventaire** : vérifier que la liste des prestataires ci-dessus reflète l'usage réel (par recoupement avec [`external-services.md`](../architecture/external-services.md) et [`provisioning.md`](../infrastructure/provisioning.md)).
2. **Certifications** : pour chaque prestataire critique, vérifier le maintien des certifications déclarées (consulter le Trust Center / page compliance officielle).
3. **SLA** : confirmer les engagements de disponibilité, et la couverture des incidents passés (consulter les status pages, recouper avec Sentry / Mattermost).
4. **RGPD / DPA** : vérifier que les DPA en vigueur sont à jour, qu'aucun sous-traitant supplémentaire non autorisé n'est introduit.
5. **Évaluation des alternatives** : pour les prestataires posant un risque (perte de certification, dégradation SLA, contentieux), évaluer une migration (ex. bascule vers une région SecNumCloud, changement de fournisseur).
6. Consigner la revue dans [`reviews.md`](reviews.md) §Exigences de sécurité des prestataires.

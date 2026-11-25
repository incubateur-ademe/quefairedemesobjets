# Gestion des incidents de sécurité

Procédure unique de traitement d'un incident de sécurité, de la détection à l'analyse post-incident : compromission d'un compte ou d'un serveur, fuite de données, secret exposé, vulnérabilité exploitée, indisponibilité d'origine malveillante.

> **Voir aussi** : [Politique de sécurité (SECURITY.md)](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md), [Plan de reprise d'activité (PRA)](pra.md), [Plan de continuité d'activité (PCA)](pca.md), [Gestion des secrets](secrets.md), [Authentification](authentication.md), [Maintien en conditions de sécurité](mco-mcs.md), [Monitoring](../infrastructure/monitoring.md).

## 1. Détection

| Canal                                  | Origine                                                                                                                                                     |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Signalement externe**                | Mail à l'adresse indiquée dans [SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md). Accusé de réception sous 72 h. |
| **Sentry**                             | Pic d'erreurs, erreurs inhabituelles (authentification, permissions, requêtes malformées).                                                                  |
| **Mattermost** `lvao-tour-de-controle` | Alertes de déploiement : échec, site indisponible après déploiement, déploiement inattendu.                                                                 |
| **Outils de l'incubateur**             | Dashlord, Purplemet, CodeQL, GitGuardian (secret exposé dans un commit). L'incubateur prévient l'équipe.                                                    |
| **Veille**                             | Avis CERT-FR, alertes des hébergeurs (Scaleway, Scalingo, GitHub), voir [Maintien en conditions de sécurité](mco-mcs.md).                                   |
| **Équipe**                             | Constat direct : compte inconnu lors d'une [revue des comptes](authentication.md), activité anormale dans les logs ou la console.                           |

Toute personne qui détecte un incident possible le signale sans attendre dans le canal Mattermost de l'équipe et à un DEV, qui devient le **pilote de l'incident** jusqu'à sa clôture ou sa passation explicite.

## 2. Qualification

Le pilote qualifie l'incident dès la prise en charge et le requalifie si les faits évoluent.

| Niveau       | Exemples                                                                                                                                                                          | Prise en charge                             |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Critique** | Compromission avérée (admin Django ou Wagtail, Scaleway, Scalingo, GitHub, bases de prod), violation de données personnelles, secret de prod publié, indisponibilité malveillante | Immédiate, y compris hors heures ouvrées    |
| **Majeur**   | Vulnérabilité exploitable sur un composant exposé sans exploitation constatée, tentative d'intrusion en cours, secret exposé à un tiers non autorisé                              | Dans la journée ouvrée                      |
| **Mineur**   | Tentative bloquée par les protections en place, vulnérabilité sur un composant non exposé, signalement sans impact confirmé                                                       | Selon les délais de [MCO / MCS](mco-mcs.md) |

La qualification note aussi si des **données personnelles** sont concernées : comptes Django / Wagtail, formulaires de contact transmis à Notion ou Tally (voir [Prestataires](providers.md)). Si oui, la notification au DPO est obligatoire (§4).

## 3. Confinement et rétablissement

| Étape                    | Actions                                                                                                                                                                                                                                                                                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Conserver les traces** | Avant toute suppression : exporter les événements Sentry, les logs Scalingo et Scaleway Cockpit, le journal d'audit GitHub. Restaurer une sauvegarde de base sur une instance séparée si la base est en cause ([Sauvegardes](backups.md)).                                                                                                        |
| **Confiner**             | Désactiver les comptes compromis ([Authentification](authentication.md)), révoquer et renouveler les secrets touchés ([PRA](pra.md) §Scénario 6, [Gestion des secrets](secrets.md)), bloquer les adresses IP en cause au niveau de nginx ([Sécurité réseau](network.md)), couper la fonctionnalité vulnérable ou passer la webapp en maintenance. |
| **Corriger**             | Appliquer le correctif et le déployer selon [MCO / MCS](mco-mcs.md).                                                                                                                                                                                                                                                                              |
| **Rétablir**             | Suivre le scénario du [PRA](pra.md) qui correspond (restauration de base, objet S3, reconstruction complète). Pendant l'incident, le [PCA](pca.md) décrit les modes dégradés acceptables.                                                                                                                                                         |
| **Vérifier**             | Healthcheck, Sentry, revue des comptes et des accès, surveillance renforcée les jours suivants.                                                                                                                                                                                                                                                   |

La communication interne pendant l'incident suit le [PRA](pra.md) §Communication d'incident.

## 4. Notifications

| Destinataire                        | Quand                                                                                                                                                                                                            | Par qui                                        |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Incubateur ADEME**                | Tout incident majeur ou critique, dès la qualification                                                                                                                                                           | Pilote de l'incident                           |
| **RSSI de l'ADEME**                 | Tout incident critique, dès la qualification. Décide d'une éventuelle déclaration à l'ANSSI (CERT-FR)                                                                                                            | Pilote ou incubateur                           |
| **DPO de l'ADEME** (rgpd@ademe.fr)  | Toute violation de données personnelles, possible ou avérée, sans délai                                                                                                                                          | Pilote de l'incident                           |
| **CNIL**                            | Violation de données personnelles présentant un risque pour les personnes : **sous 72 h** après sa découverte ([RGPD art. 33](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre4#Article33)) | ADEME (responsable de traitement), via son DPO |
| **Personnes concernées**            | Violation de données présentant un risque élevé pour elles (RGPD art. 34)                                                                                                                                        | ADEME, via son DPO                             |
| **Auteur d'un signalement externe** | Accusé de réception sous 72 h, puis suivi jusqu'à la correction ([SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md))                                                   | Équipe                                         |

Le délai de 72 h de la CNIL court dès que l'équipe a connaissance de la violation : le DPO est prévenu le jour même pour pouvoir le tenir.

## 5. Journalisation

Chaque incident, quel que soit son niveau, est consigné dans le **« Registre des incidents de sécurité »** de l'incubateur ADEME, dans Notion, à l'ouverture puis mis à jour jusqu'à la clôture :

- dates de détection, de qualification et de clôture ;
- canal de détection et pilote ;
- niveau, description, périmètre touché, données personnelles concernées ou non ;
- actions de confinement et de rétablissement ;
- notifications envoyées (destinataire, date) ;
- lien vers l'analyse post-incident.

## 6. Analyse post-incident

Pour tout incident majeur ou critique, l'équipe rédige une analyse dans les 2 semaines qui suivent la clôture :

1. Chronologie des faits, de la première trace à la clôture.
2. Cause racine et facteurs aggravants.
3. Ce qui a fonctionné, ce qui a manqué (détection, outils, accès, documentation).
4. **Plan d'action** : chaque action a un responsable et une échéance, et fait l'objet d'une issue suivie jusqu'à sa clôture.
5. Mise à jour de la documentation concernée (cette procédure, [PRA](pra.md), [PCA](pca.md), [MCO / MCS](mco-mcs.md)).

L'analyse est liée depuis l'entrée du registre et partagée avec l'incubateur.

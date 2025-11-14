# Jeu de données open data : acteurs

## Présentation

- **Finalité** : partager en open data la liste des acteurs de l'économie circulaire collectée par l'équipe Longue Vie Aux Objets (ADEME) avec leurs métadonnées principales.
- **Couverture** : acteurs actifs après déduplication et consolidation multi-sources (au moins 250 000 acteurs). Seules les données partagées en licences ouvertes sont mises à disposition.
- **Diffusion** : publication hebdomadaire (chaque lundi matin).
- **Licence et paternité** : diffusion sous licence ouverte ADEME ; la colonne `paternite` liste les contributeurs à la donnée compilée de chaque acteur. # Obligation de mentionner la paternité lors de la réutilisation de celle-ci.

## Schéma des colonnes

### Identification

| Colonne                          | Type  | Description                                             | Format ou valeurs                                                                |
| -------------------------------- | ----- | ------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `identifiant`                    | texte | Identifiant stable (base57) de l'acteur.                | Exemple : `aDcrby2bghAZFM3yYCRTue`.                                              |
| `paternite`                      | texte | Paternité juridique du jeu de données.                  | `Longue Vie Aux Objets\|ADEME\|<libelle_source_1>\|...`.                         |
| `identifiants_des_contributeurs` | jsonb | Identifiants des sources ayant contribuées à la donnée. | Ex. `[{"ECOMAISON": "1234567890"}, {"REFASHION": "TLC-REFASHION-PAV-1234567"}]`. |
| `nom`                            | texte | Nom de l'acteur.                                        | Texte libre, non vide.                                                           |
| `nom_commercial`                 | texte | Enseigne commerciale (si différente).                   | Texte libre ; peut être vide.                                                    |
| `siren`                          | texte | Identifiant SIREN (9 chiffres).                         | Vide si non connu.                                                               |
| `siret`                          | texte | Identifiant SIRET (14 caractères).                      | Vide si non connu.                                                               |
| `description`                    | texte | Description libre de l'acteur.                          | Peut être vide.                                                                  |
| `type_dacteur`                   | texte | Type fonctionnel de l'acteur.                           | Voir section "Valeurs de référence".                                             |

### Localisation et contact

| Colonne               | Type  | Description                                    | Format ou valeurs                                                                                                                              |
| --------------------- | ----- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `site_web`            | texte | URL publique.                                  | URL absolue ou vide.                                                                                                                           |
| `telephone`           | texte | Numéro de téléphone fixe partageable.          | Vide si portable (06/07).                                                                                                                      |
| `adresse`             | texte | Adresse postale.                               | Peut être vide.                                                                                                                                |
| `complement_dadresse` | texte | Complément d'adresse.                          | Peut être vide.                                                                                                                                |
| `code_postal`         | texte | Code postal.                                   | Format `XXXXX`.                                                                                                                                |
| `ville`               | texte | Commune.                                       | Texte libre.                                                                                                                                   |
| `code_commune`        | texte | Code INSEE (5 caractères).                     | Peut être vide.                                                                                                                                |
| `code_epci`           | texte | Code EPCI rattaché.                            | Vide si non renseigné.                                                                                                                         |
| `nom_epci`            | texte | Nom de l'EPCI.                                 | Vide si non renseigné.                                                                                                                         |
| `latitude`            | float | Latitude WGS84.                                | Peut être nulle si la géolocalisation est absente.                                                                                             |
| `longitude`           | float | Longitude WGS84.                               | Peut être nulle si la géolocalisation est absente.                                                                                             |
| `perimetreadomicile`  | jsonb | Liste de périmètres d'intervention à domicile. | Tableau `[{"type": "KILOMETRIQUE", "valeur": "30"}, ...]`. Types admis : `DEPARTEMENTAL`, `KILOMETRIQUE`, `FRANCE_METROPOLITAINE`, `DROM_TOM`. |

### Offre de services et labels

| Colonne                                                                                                             | Type    | Description                                         | Format ou valeurs                                                                                          |
| ------------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `qualites_et_labels`                                                                                                | texte   | Codes de labels et qualités.                        | Codes séparés par `\|` (ex. `ess\|qualirepar`). Voir section "Valeurs de référence".                       |
| `public_accueilli`                                                                                                  | texte   | Public cible (particuliers, pro, etc.).             | Valeurs admises : `Particuliers`, `Professionnels`, `Particuliers et professionnels`. Peut être vide.      |
| `reprise`                                                                                                           | texte   | Mention de reprise.                                 | Valeurs admises : ``, `1 pour 0`, `1 pour 1`.                                                              |
| `exclusivite_de_reprisereparation`                                                                                  | boolean | Exclusivité de reprise/réparation.                  | `true` ou `false`.                                                                                         |
| `uniquement_sur_rdv`                                                                                                | boolean | Nécessite de RDV.                                   | `true` ou `false`.                                                                                         |
| `type_de_services`                                                                                                  | texte   | Codes de services disponibles.                      | Codes séparés par `\|` (ex. `recyclerie\|structure_de_collecte`). Voir section "Valeurs de référence".     |
| `consignes_dacces`                                                                                                  | texte   | Consignes pratiques d'accès.                        | Peut être vide.                                                                                            |
| `horaires_description`                                                                                              | texte   | Horaires lisibles.                                  | Ex. `mercredi 10h00-18h00 samedi 10h00-18h00`.                                                             |
| `horaires_osm`                                                                                                      | texte   | Horaires au format OpenStreetMap.                   | Référence : <https://wiki.openstreetmap.org/wiki/Key:opening_hours>.                                       |
| `lieu_prestation`                                                                                                   | texte   | Mode de prestation.                                 | Valeurs de l'énum : `A_DOMICILE`, `SUR_PLACE`, `SUR_PLACE_OU_A_DOMICILE` (ou vide).                        |
| `propositions_de_services`                                                                                          | texte   | Représentation JSON des actions et sous-catégories. | Chaîne JSON, ex. `[{"action":"donner","sous_categories":["vetement", ...]}, ...]`.                         |
| `emprunter`, `preter`, `louer`, `mettreenlocation`, `reparer`, `donner`, `trier`, `echanger`, `revendre`, `acheter` | texte   | Sous-catégories associées à chaque action.          | Codes séparés par `\|` (ex. `vetement\|linge_de_maison`). Valeur vide si l'acteur ne propose pas l'action. |

### Métadonnées

| Colonne                         | Type  | Description                          | Format               |
| ------------------------------- | ----- | ------------------------------------ | -------------------- |
| `date_de_derniere_modification` | texte | Date de dernière mise à jour connue. | Format `YYYY-MM-DD`. |

## Valeurs de référence

### Types d'acteur (`type_dacteur`)

- `acteur_digital` : acteur opérant exclusivement en ligne.
- `artisan` : artisan ou commerce indépendant.
- `collectivite` : collectivité ou établissement public.
- `commerce` : commerce de détail multi-sites.
- `ess` : acteur de l'économie sociale et solidaire.
- `pav_public` : point d'apport volontaire public.
- `decheterie`, `ets_sante`, `plateforme_inertes`, `pav_prive`, `pav_ponctuel` : catégories spécifiques pouvant apparaître selon les sources.

### Labels (`qualites_et_labels`)

Codes renvoyés sous forme de chaîne séparée par `|`. Correspondances principales observées dans les fixtures :

- `reparacteur` : labellisé Répar'acteur (CMA).
- `qualirepar` : bonus réparation QualiRépar.
- `refashion` : bonus réparation Re_fashion textile.
- `ecomaison` : bonus réparation EcoMaison.
- `bonusrepar_ABJ_TH` : bonus réparation bricolage & jardinage thermique (Ecologic).
- `BonusRepar_ASL` : bonus réparation Sport & Loisirs (Ecologic).
- `ess` : enseigne de l'économie sociale et solidaire.

> D'autres codes peuvent être ajoutés au fil des conventions partenaires

### Services (`type_de_services`)

Quelques codes fréquents issus de `qfdmo_acteurservice` :

- `recyclerie` : collecte et vente en ressourcerie.
- `structure_de_collecte` : apport volontaire ou collecte organisée.
- `espace_de_partage` : emprunt/prêt/échanges entre usagers.
- `service_de_reparation` : atelier de réparation professionnelle.
- `location_professionnel` : location d'objets via un professionnel.
- (Voir la table complète pour les autres codes : `achat_revente_particuliers`, `atelier_pour_reparer_soi_meme`, etc.).

### Actions et sous-catégories

- Actions possibles : `acheter`, `donner`, `emprunter`, `louer`, `mettreenlocation`, `preter`, `reparer`, `trier`, `echanger`, `revendre`.
- Les sous-catégories sont les codes d'objets de `qfdmo_souscategorieobjet` (ex. `vetement`, `outil_de_bricolage_et_jardinage`, `abj_electrique`, `smartphone_tablette_et_console`, `gros_electromenager_refrigerant`). Elles sont ordonnées et dédupliquées avant export.

### Périmètre à domicile (`perimetreadomicile`)

- `DEPARTEMENTAL` : valeur = code département (ex. `29`, `2A`).
- `KILOMETRIQUE` : valeur = rayon en kilomètres (chaîne numérique, ex. `30`).
- `FRANCE_METROPOLITAINE` : valeur vide (`""`).
- `DROM_TOM` : valeur vide (`""`).

## Exemple d'enregistrement

Acteur issu des fixtures (`qfdmo/fixtures/acteurs.json`) :

```json
{
  "identifiant": "aDcrgdtbqxAZFM3yYCRTue",
  "paternite": "Longue Vie Aux Objets|ADEME|ADEME - SINOE|ECOMAISON|ECOLOGIC|ECOSYSTEM|REFASHION",
  "identifiants_des_contributeurs": [
    { "ADEME - SINOE": "SINOE-12345-123" },
    { "ECOMAISON": "1234567890" },
    { "ECOLOGIC": "EC-12345-1234" },
    { "ECOSYSTEM": "ES-12345-1234" },
    { "REFASHION": "TLC-REFASHION-PAV-1234567" }
  ],
  "nom": "ASSOCIATION RESSOURCERIE",
  "nom_commercial": "Ressourcerie",
  "siren": "123456789",
  "siret": "12345678900001",
  "type_dacteur": "ess",
  "site_web": "https://www.ressourcerie.com/",
  "telephone": null,
  "adresse": "1 rue du Général De Gaulle",
  "code_postal": "12345",
  "ville": "Ville sur Fleuve",
  "latitude": 47.1234567,
  "longitude": -2.7654321,
  "type_de_services": "recyclerie|structure_de_collecte",
  "qualites_et_labels": "ess",
  "propositions_de_services": "[{\"action\":\"acheter\",\"sous_categories\":[\"vetement\",...]}...]",
  "donner": "vetement|linge_de_maison|chaussures",
  "trier": "vetement|linge_de_maison|chaussures",
  "acheter": "vetement|vaisselle|meuble|...",
  "date_de_derniere_modification": "2025-06-24"
}
```

> Les identifiants externes et certaines sous-catégories ci-dessus sont indiqués à titre illustratif ; se référer aux exports réels pour leurs valeurs exactes.

## Points d'attention pour les réutilisateurs

- `telephone` est volontairement vide lorsque la source ne permet pas la diffusion (mobiles commençant par 06/07 ou sources `carteco`).
- `propositions_de_services` est une chaîne JSON : la parser avant usage pour reconstituer la structure originale (`action` + `sous_categories`).
- Les colonnes par action (`donner`, `reparer`, etc.) ne contiennent que des codes.
- `perimetreadomicile` peut être absent si l'acteur n'intervient pas à domicile.
- Les labels et services sont dédupliqués mais peuvent être vides : tester la présence avant d'afficher des pictogrammes.

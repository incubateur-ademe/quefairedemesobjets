# Jeu de donnees open data : acteurs

## Presentation

- **Finalité** : partager en open data la liste des acteurs de l'économie circulaire collectés par l'équipe Longue Vie Aux Objets (ADEME) avec leurs métadonnées principales.
- **Couverture** : acteurs actifs apres déduplication et consolidation multi-sources (au moins 250 000 acteurs). Seules les données partagées en licences ouvertes sont mises à disposition.
- **Diffusion** : publication hebdomadaire (chaque lundi matin).
- **Licence et paternité** : diffusion sous licence ouverte ADEME ; la colonne `paternite` liste les contributeurs à la donnée compilée de chaque acteur. # Obligation de mentionner la parternité lors de la ré-utilisation de celle-ci.

## Schema des colonnes

### Identification

| Colonne                          | Type  | Description                                             | Format ou valeurs                                                                |
| -------------------------------- | ----- | ------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `identifiant`                    | texte | Identifiant stable (base57) de l'acteur.                | Exemple : `aDcrby2bghAZFM3yYCRTue`.                                              |
| `paternite`                      | texte | Paternité juridique du jeu de donnees.                  | `Longue Vie Aux Objets\|ADEME\|<libelle_source_1>\|...`.                         |
| `identifiants_des_contributeurs` | jsonb | Identifiants des sources ayant contribuées à la donnée. | Ex. `[{"ECOMAISON": "1234567890"}, {"REFASHION": "TLC-REFASHION-PAV-1234567"}]`. |
| `nom`                            | texte | Nom de l'acteur.                                        | Texte libre, non vide.                                                           |
| `nom_commercial`                 | texte | Enseigne commerciale (si différente).                   | Texte libre ; peut etre vide.                                                    |
| `siren`                          | texte | Identifiant SIREN (9 chiffres).                         | Vide si non connu.                                                               |
| `siret`                          | texte | Identifiant SIRET (14 caracteres).                      | Vide si non connu.                                                               |
| `description`                    | texte | Description libre de l'acteur.                          | Peut etre vide.                                                                  |
| `type_dacteur`                   | texte | Type fonctionnel de l'acteur.                           | Voir section "Valeurs de reference".                                             |

### Localisation et contact

| Colonne               | Type  | Description                                    | Format ou valeurs                                                                                                                              |
| --------------------- | ----- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `site_web`            | texte | URL publique.                                  | URL absolue ou vide.                                                                                                                           |
| `telephone`           | texte | Numero telephone fixe partageable.             | Vidé si portable (06/07).                                                                                                                      |
| `adresse`             | texte | Adresse postale.                               | Peut etre vide.                                                                                                                                |
| `complement_dadresse` | texte | Complement d'adresse.                          | Peut etre vide.                                                                                                                                |
| `code_postal`         | texte | Code postal.                                   | Format `XXXXX`.                                                                                                                                |
| `ville`               | texte | Commune.                                       | Texte libre.                                                                                                                                   |
| `code_commune`        | texte | Code INSEE (5 caracteres).                     | Peut etre vide.                                                                                                                                |
| `code_epci`           | texte | Code EPCI rattache.                            | Vide si non renseigne.                                                                                                                         |
| `nom_epci`            | texte | Nom de l'EPCI.                                 | Vide si non renseigne.                                                                                                                         |
| `latitude`            | float | Latitude WGS84.                                | Peut etre null si geolocalisation absente.                                                                                                     |
| `longitude`           | float | Longitude WGS84.                               | Peut etre null si geolocalisation absente.                                                                                                     |
| `perimetreadomicile`  | jsonb | Liste de perimetres d'intervention a domicile. | Tableau `[{"type": "KILOMETRIQUE", "valeur": "30"}, ...]`. Types admis : `DEPARTEMENTAL`, `KILOMETRIQUE`, `FRANCE_METROPOLITAINE`, `DROM_TOM`. |

### Offre de services et labels

| Colonne                                                                                                             | Type    | Description                                         | Format ou valeurs                                                                                          |
| ------------------------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `qualites_et_labels`                                                                                                | texte   | Codes de labels et qualites.                        | Codes separes par `\|` (ex. `ess\|qualirepar`). Voir section "Valeurs de reference".                       |
| `public_accueilli`                                                                                                  | texte   | Public cible (particuliers, pro, etc.).             | Valeurs admises: `Particuliers`, `Professionnels`, `Particuliers et professionnels`. peut être vide.       |
| `reprise`                                                                                                           | texte   | Mention de reprise.                                 | Valeurs admises : ``, `1 pour 0`, `1 pour 1`.                                                              |
| `exclusivite_de_reprisereparation`                                                                                  | boolean | Exclusivite de reprise/reparation.                  | `true` ou `false`.                                                                                         |
| `uniquement_sur_rdv`                                                                                                | boolean | Necessite de RDV.                                   | `true` ou `false`.                                                                                         |
| `type_de_services`                                                                                                  | texte   | Codes de services disponibles.                      | Codes separes par `\|` (ex. `recyclerie\|structure_de_collecte`). Voir section "Valeurs de reference".     |
| `consignes_dacces`                                                                                                  | texte   | Consignes pratiques d'acces.                        | Peut etre vide.                                                                                            |
| `horaires_description`                                                                                              | texte   | Horaires lisibles.                                  | Ex. `mercredi 10h00-18h00 samedi 10h00-18h00`.                                                             |
| `horaires_osm`                                                                                                      | texte   | Horaires au format OpenStreetMap.                   | Reference : <https://wiki.openstreetmap.org/wiki/Key:opening_hours>.                                       |
| `lieu_prestation`                                                                                                   | texte   | Mode de prestation.                                 | Valeurs de l'enum : `A_DOMICILE`, `SUR_PLACE`, `SUR_PLACE_OU_A_DOMICILE` (ou vide).                        |
| `propositions_de_services`                                                                                          | texte   | Representation JSON des actions et sous-categories. | Chaine JSON, ex. `[{"action":"donner","sous_categories":["vetement", ...]}, ...]`.                         |
| `emprunter`, `preter`, `louer`, `mettreenlocation`, `reparer`, `donner`, `trier`, `echanger`, `revendre`, `acheter` | texte   | Sous-categories associees a chaque action.          | Codes separes par `\|` (ex. `vetement\|linge_de_maison`). Valeur vide si l'acteur ne propose pas l'action. |

### Metadonnees

| Colonne                         | Type  | Description                          | Format               |
| ------------------------------- | ----- | ------------------------------------ | -------------------- |
| `date_de_derniere_modification` | texte | Date de derniere mise a jour connue. | Format `YYYY-MM-DD`. |

## Valeurs de reference

### Types d'acteur (`type_dacteur`)

- `acteur_digital` : acteur operant exclusivement en ligne.
- `artisan` : artisan ou commerce independant.
- `collectivite` : collectivite ou etablissement public.
- `commerce` : commerce de detail multi-sites.
- `ess` : acteur de l'economie sociale et solidaire.
- `pav_public` : point d'apport volontaire public.
- `decheterie`, `ets_sante`, `plateforme_inertes`, `pav_prive`, `pav_ponctuel` : categories specifques pouvant apparaitre selon les sources.

### Labels (`qualites_et_labels`)

Codes renvoyes sous forme de chaine separee par `|`. Correspondances principales observees dans les fixtures :

- `reparacteur` : Labellise Repare'Acteur (CMA).
- `qualirepar` : Bonus Reparation QualiRepar.
- `refashion` : Bonus Reparation Re_fashion textile.
- `ecomaison` : Bonus Reparation EcoMaison.
- `bonusrepar_ABJ_TH` : Bonus Reparation bricolage & jardinage thermique (Ecologic).
- `BonusRepar_ASL` : Bonus Reparation Sport & Loisirs (Ecologic).
- `ess` : Enseigne de l'economie sociale et solidaire.

> D'autres codes peuvent etre ajoutes au fil des conventions partenaires ; se referer a la table `qfdmo_labelqualite` pour la liste exhaustive.

### Services (`type_de_services`)

Quelques codes frequents issus de `qfdmo_acteurservice` :

- `recyclerie` : collecte et vente en ressourcerie.
- `structure_de_collecte` : apport volontaire ou collecte organisee.
- `espace_de_partage` : emprunt/pret/echanges entre usagers.
- `service_de_reparation` : atelier de reparation professionnelle.
- `location_professionnel` : location d'objets via un professionnel.
- (Voir la table complete pour les autres codes : `achat_revente_particuliers`, `atelier_pour_reparer_soi_meme`, etc.).

### Actions et sous-categories

- Actions possibles : `acheter`, `donner`, `emprunter`, `louer`, `mettreenlocation`, `preter`, `reparer`, `trier`, `echanger`, `revendre`.
- Les sous-categories sont les codes d'objets de `qfdmo_souscategorieobjet` (ex. `vetement`, `outil_de_bricolage_et_jardinage`, `abj_electrique`, `smartphone_tablette_et_console`, `gros_electromenager_refrigerant`). Elles sont ordonnees et dedupees avant export.

### Perimetre a domicile (`perimetreadomicile`)

- `DEPARTEMENTAL` : valeur = code departement (ex. `29`, `2A`).
- `KILOMETRIQUE` : valeur = rayon en kilometres (chaine numerique, ex. `30`).
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

> Les identifiants externes et certaines sous-categories ci-dessus sont indiques a titre illustratif ; se referer aux exports reels pour leurs valeurs exactes.

## Points d'attention pour les reutilisateurs

- `telephone` est volontairement vide lorsque la source ne permet pas la diffusion (mobiles commençant par 06/07 ou sources `carteco`).
- `propositions_de_services` est une chaine JSON : la parser avant usage pour reconstituer la structure originale (`action` + `sous_categories`).
- Les colonnes par action (`donner`, `reparer`, etc.) ne contiennent que des codes.
- `perimetreadomicile` peut etre absent si l'acteur n'intervient pas a domicile.
- Les labels et services sont dedupes mais peuvent etre vides : tester la presence avant d'afficher des pictogrammes.

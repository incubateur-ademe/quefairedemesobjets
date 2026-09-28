# Jeu de données open data : fiches objets et déchets (produits et consignes)

## Présentation

- **Finalité** : partager en open data les fiches « Que faire de mes objets et déchets » (ADEME) et leurs consignes, geste par geste : réparer, donner, revendre, déposer…
- **Couverture** : toutes les fiches publiées sur le site, familles comprises, et chaque consigne saisie dans un bloc « Grille de consignes » du CMS.
- **Diffusion** : publication hebdomadaire (chaque lundi matin), en même temps que le jeu de données des acteurs.
- **Licence et paternité** : diffusion sous licence ouverte ADEME. Paternité : `Que faire de mes objets et déchets|ADEME`.
- **Structure** : deux tables. `produits.csv` liste les fiches ; `consignes.csv` liste les consignes, chacune renvoyant à sa fiche par `identifiant_produit`. Les mêmes lignes sont servies par l'[API v1](../apis/v1.md) (`/api/v1/produits`, `/api/v1/consignes`).

Le jeu de données suit le [guide de qualité de data.gouv.fr](https://guides.data.gouv.fr/guides/guide-qualite/preparer-un-jeu-de-donnees-de-qualite/structurer-un-jeu-de-donnees) : en-têtes en minuscules sans accent, UTF-8, virgule comme séparateur, cellule vide pour une valeur inconnue, valeurs multiples séparées par `|` comme dans le jeu de données des acteurs.

### Variables pivots vers le jeu de données des acteurs

Deux colonnes permettent de joindre ces tables au jeu de données [Acteurs de l'économie circulaire](https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire) :

- `produits.sous_categories` contient les codes de sous-catégories d'objets, ceux des colonnes par action des acteurs (`vetement`, `emballage_plastique`…) ;
- `consignes.gestes` contient les codes d'action des acteurs (`reparer`, `donner`, `revendre`, `trier`…).

Pour une consigne, les lieux qui la mettent en œuvre sont donc les acteurs dont la colonne de chaque geste contient l'une des sous-catégories de la fiche.

## Table `produits.csv`

| Colonne                         | Type   | Description                                                | Format ou valeurs                         |
| ------------------------------- | ------ | ---------------------------------------------------------- | ----------------------------------------- |
| `identifiant`                   | entier | Identifiant stable de la fiche.                            | Ex. `248`.                                |
| `nom`                           | texte  | Titre de la fiche.                                         | Texte libre, non vide.                    |
| `url`                           | texte  | Adresse de la fiche sur le site.                           | URL absolue.                              |
| `type`                          | texte  | Objet ou déchet (à usage unique).                          | `objet` ou `dechet`.                      |
| `identifiant_famille`           | entier | Identifiant de la fiche famille qui la regroupe.           | Vide pour une fiche de premier niveau.    |
| `synonymes`                     | texte  | Autres noms sous lesquels la fiche est trouvée.            | Séparés par `\|`, triés ; peut être vide. |
| `sous_categories`               | texte  | Codes de sous-catégories d'objets, pivot vers les acteurs. | Séparés par `\|`, triés ; peut être vide. |
| `date_de_derniere_modification` | texte  | Date de dernière publication.                              | `YYYY-MM-DD` ; peut être vide.            |

## Table `consignes.csv`

| Colonne               | Type    | Description                                                     | Format ou valeurs                                                     |
| --------------------- | ------- | --------------------------------------------------------------- | --------------------------------------------------------------------- |
| `identifiant`         | texte   | Identifiant stable de la consigne, attribué par le CMS.         | UUID.                                                                 |
| `identifiant_produit` | entier  | Fiche à laquelle la consigne appartient.                        | Clé vers `produits.identifiant`.                                      |
| `ordre`               | entier  | Position de la consigne dans la fiche.                          | À partir de `1`.                                                      |
| `titre`               | texte   | Titre de la consigne.                                           | Non vide.                                                             |
| `contenu`             | texte   | Contenu mis en forme.                                           | HTML : paragraphes, gras, liens, listes.                              |
| `contenu_texte`       | texte   | Le même contenu en texte brut.                                  | Une ligne par paragraphe, items de liste préfixés par `- `.           |
| `gestes`              | texte   | Codes d'action décrits par la consigne, pivot vers les acteurs. | Séparés par `\|`. Voir section « Valeurs de référence ».              |
| `etat`                | texte   | État de l'objet auquel la consigne s'applique.                  | `reparable`, `bon_etat`, `mauvais_etat` ou vide (déchets).            |
| `lieu_de_depot`       | texte   | Où déposer le déchet.                                           | Code du lieu ou vide (objets). Voir section « Valeurs de référence ». |
| `bonus_reparation`    | booléen | La fiche est éligible au bonus réparation pour ce geste.        | `true` ou `false`.                                                    |
| `lien_url`            | texte   | Page du site vers laquelle la consigne renvoie.                 | URL absolue ou vide.                                                  |

## Valeurs de référence

### Gestes (`gestes`)

Les codes d'action du jeu de données des acteurs : `reparer`, `donner`, `echanger`, `rapporter`, `revendre`, `acheter`, `preter`, `emprunter`, `louer`, `mettreenlocation`, `trier`. « Déposer » dans l'interface correspond à `trier`.

### États (`etat`)

- `reparable` : l'objet est abîmé mais réparable.
- `bon_etat` : l'objet fonctionne encore.
- `mauvais_etat` : l'objet est hors d'usage.

### Lieux de dépôt (`lieu_de_depot`)

Les codes sont gérés dans le CMS (`Lieux de dépôt`) et apparaissent dans l'export au fur et à mesure de leur création. Ceux relevés sur les fiches existantes : `bac_de_tri`, `conteneur_a_verre`, `decheterie`, `point_de_collecte`, `ordures_menageres`, `magasin`, `bac_de_compostage`, `bois_de_chauffage`, `entre_particuliers`, `reemploi`, `structure_de_reemploi`, `etablissement_de_sante`.

## Exemple d'enregistrements

`produits.csv` :

```csv
identifiant,nom,url,type,identifiant_famille,synonymes,sous_categories,date_de_derniere_modification
248,Emballages,https://quefairedemesdechets.ademe.fr/emballages/,dechet,,emballage,emballage_carton|emballage_plastique,2026-09-22
```

`consignes.csv` :

```csv
identifiant,identifiant_produit,ordre,titre,contenu,contenu_texte,gestes,etat,lieu_de_depot,bonus_reparation,lien_url
3f1c…,248,1,Emballages en verre,"<p>Dans le <b>conteneur à verre</b></p>","Dans le conteneur à verre",trier,,conteneur_a_verre,false,https://quefairedemesdechets.ademe.fr/emballages-en-verre/
```

## Points d'attention pour les réutilisateurs

- Une fiche peut porter plusieurs consignes pour un même geste, par exemple un bloc par lieu de dépôt : `gestes` ne suffit pas à identifier une consigne, `identifiant` si.
- `contenu` est du HTML : préférer `contenu_texte` pour un affichage brut.
- Les fiches sans bloc « Grille de consignes » n'ont pas encore de lignes dans `consignes.csv` : la migration des fiches existantes est progressive.

## Migration des fiches existantes

Dans le CMS, l'action de page « Convertir les cartes en grille de consignes » déplace la première rangée de cartes d'une fiche (après l'introduction, avant la carte) dans une grille de consignes, largeur de colonne comprise : titre, contenu et lien ne sont pas réécrits, et les cartes plus bas dans la page ne sont pas touchées. Les champs typés sont déduits des badges selon les règles de migration de la tâche #3284, sans intervention d'un modèle : état et bonus d'après les badges pour un objet (ou d'après le titre « Réparer », « Donner ou revendre », « Déposer » à défaut), lieu de dépôt d'après le premier badge qui nomme un lieu pour un déchet, gestes déduits de l'état ou « déposer » (`trier`), « rapporter » quand la carte dit de rapporter le produit. Une carte dont l'état ne peut pas être déduit reste en place et est signalée à l'éditeur ; il en va de même quand les badges contredisent le type de la fiche (lieu de dépôt sur une fiche objet, état sur une fiche déchet), signe que la case « À usage unique » est à revoir avant de convertir. Le résultat est un **brouillon** que l'éditeur relit avant de publier (`webapp/qfdmd/consignes_migration.py`).

## Production

Les lignes sont construites par `webapp/qfdmd/opendata.py` et servies par `webapp/qfdmd/api.py`. Le DAG `export_opendata_dag` (`data-platform/dags/acteurs/dags/export_opendata.py`) télécharge `/api/v1/produits.csv` et `/api/v1/consignes.csv` et les dépose dans le bucket `lvao-opendata`, répertoire `fiches/`.

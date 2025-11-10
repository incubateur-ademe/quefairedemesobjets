# Politique de version du jeu de données Open Data

Cette page explique comment évoluent les données « Acteurs de l'économie circulaire - Longue Vie Aux Objets » et ce que cela implique pour leurs réutilisateurs.

## 1. Mises à jour du contenu

- Les valeurs et enregistrements sont rafraîchis chaque semaine.
- Ces mises à jour n’entraînent pas de changement de version : le schéma reste identique et l’URL ne change pas.
- Aucune action technique n’est attendue de votre part.

## 2. Mises à jour de la structure (schéma)

Nous distinguons deux familles de modifications :

- **Changements compatibles** : ils n’interrompent pas vos traitements existants.
  - Exemples : ajout d’une colonne facultative, augmentation de la longueur d’un champ texte, ajout d’une nouvelle valeur autorisée.
  - Nous n’incrémentons pas la version. Une notification peut être envoyée pour vous informer du changement.
- **Changements majeurs** : ils exigent une adaptation de vos scripts ou interfaces.
  - Exemples : suppression ou renommage d’une colonne, changement de type (texte → entier), modification d’une contrainte obligatoire.
  - Une nouvelle version du jeu de données est publiée.

Toutes les évolutions (qu’elles soient compatibles ou majeures) sont consignées et datées dans un changelog joint au jeu de données.

## 3. Gestion des versions

- Chaque version majeure correspond à un nouveau jeu de données.
- Le numéro de version figure dans le titre, par exemple :
  - `Acteurs de l'économie circulaire - Longue Vie Aux Objets - Version 1`
  - `Acteurs de l'économie circulaire - Longue Vie Aux Objets - Version 2`

## 4. Cycle de vie d’une version

- Nous maintenons simultanément la version N (active) et la version N-1 (dépréciée).
- La version dépréciée reste accessible pendant 6 mois pour vous laisser le temps de migrer.
- Passé ce délai, la version dépréciée est supprimée définitivement.
- Les versions actives et dépréciées continuent d’être alimentées en données hebdomadaires jusqu’à leur retrait.

# Organisation interne de la gestion des versions du jeu de données Open Data

> ⚠️⚠️⚠️ Créer une nouvelle version du jeu de données Open Data est un processus lourd : on évite tant que possible d’en créer de nouvelles.
>
> La création d’une nouvelle version doit être une décision collégiale de l’équipe Longue vie aux objets.

En complément de la [Politique de version du jeu de données Open Data](./politique-de-version-du-jeu-de-donnees-open-data.md)

les données sont diffusées sur data.ademe.fr (Koumoul) et sur data.gouv.fr via un processus de miroir (Koumoul met à jour les données sur data.gouv.fr)

## Gestion des versions mineures : mise à jour du changelog

La mise à jour du changelog est assurée par Christian Charousset pour les évolutions et modifications métier (ex. : ajout d'une source) et Nicolas Oudard pour les évolutions techniques : évolution du schéma de données.

## Les difficultés de la mise en place d’un versionning (version majeure)

- Chaque version est un nouveau jeu de données sur Koumoul et [data.gouv.fr](http://data.gouv.fr) → chronophage
  - sur Koumoul : c’est un nouveau jeu de données
  - sur [data.gouv.fr](http://data.gouv.fr) : c’est un nouveau fichier dans un jeu de données
- On doit générer et publier autant de fois qu’il y a de versions
- On doit maintenir un calendrier des versions dépréciées à supprimer

## Communications

On ne peut communiquer qu’aux utilisateurs qui se sont identifiés comme réutilisateurs

- Communication optionnelle pour les modifications retro-compatibles
- [Obligatoire] Communication lors de la publication d’une nouvelle version et de la dépréciation de la version précédente
- [Obligatoire] Communication avant et lors de la suppression d’une version dépréciée

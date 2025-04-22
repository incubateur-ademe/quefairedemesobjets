# Deploiement

## Déploiement sur Scalingo

Nous avons besoin d'installer GDAL comme c'est expliqué dans la doc suivante : [https://techilearned.com/configure-geodjango-in-scalingo/](https://techilearned.com/configure-geodjango-in-scalingo/) cf. [https://doc.scalingo.com/platform/app/app-with-gdal](https://doc.scalingo.com/platform/app/app-with-gdal)

le code est déployé en preprod lors de la mise à jour de la branche main

et en production quand il est tagué avec en respectant le format de version semantique vX.Y.Z

### Déploiement du code de l'interface

le code de l'interface est déployé sur le repo git de scalingo à conditions que les tests soit passés avec succès via Github

## Déploiement sur CleverCloud

<!-- TODO data plateforme -->

## Deploiment sur Scaleway

<!-- TODO s3 et bientôt plus ? -->

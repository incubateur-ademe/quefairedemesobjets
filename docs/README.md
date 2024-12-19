# Documentation technique de l'application

```{toctree}
:hidden:

comment-faire/README
explications/README
reference/README
tutoriels/README
```

## Par ou commencer ?

Cette documentation aide les développeurs et toute personne s'intéressant à la construction technique de la plateforme à comprendre son architecture, son fonctionnement et les prises de décision qui y ont abouties.

Elle est répartie en 4 sections suivant la convention [DIATAXIS](https://diataxis.fr)

![](https://diataxis.fr/_images/diataxis.png)

Pour en savoir plus sur la construction de cette documentation, suivez le guide : [Guide de la documentation technique](./reference/901-documentation-technique.md)

## Référence

Contient toute la description technique de l'application, par exemple :

- Architecture des fichiers
- Architecture des données
- Conventions de code et de base de données
…

## Explications

Description de comment ça marche et des prises de décision, par exemple :

- Pourquoi ce choix d'architecture des données
- Principe sanitaire mise en place sur la platefome données
…

## Comment faire ?

Guide l'utilisateur pour résoudre un problème, par exemple :

- Copie de la base de données de prod vers preprod
- Debugage
…

## Tutoriels

Décrit les apprentissages pas à pas de l'utilisation des outils, par exemple

- Installation d'un poste développeur
- Mise en production
…

## Sommaire

- [🧐 REFERENCE](./reference/README.md)
  - [Règles de codage](./reference/101-coding-guidelines.md)
  - [Frontend et templating](./reference/201-frontend.md)
  - [Règle de codage de la base de données](./reference/301-db-guidelines.md)
  - [Architecture des fichiers de code de la partie data](./reference/302-organisations-des-fichiers-data.md)
  - [Guide de la docmentation technique](./reference/901-documentation-technique.md)

- [❓ EXPLICATIONS](./explications/README.md)

- [🤔 COMMENT FAIRE ?](./comment-faire/README.md)
  - [Commandes Django utiles](./comment-faire/101-commandes-django.md)

- [🙌 TUTORIELS](./tutoriels/README.md)

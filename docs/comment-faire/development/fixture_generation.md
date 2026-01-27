# Utiliser les fixtures

Le projet utilise des fixtures Django[^1] pour les tests.
Celles-ci sont basées sur de la donnée issue de la base de production afin de tester l'application sur des situations _de la vraie vie_.

## Générer des fixtures, cas général

Toutes les fixtures à l'exception des `DisplayedActeur` (acteurs affichés) et `DisplayedPropositionService` (proposition de service de ces acteurs) peuvent être générées à partir d'une commande `make` :

```sh
make generate-fixtures

# il est conseillé de conserver dans git les fixtures à jour, et d'embarquer
# ces mises à jour dans les pull request.
git add qfdmo/fixtures qfdmd/fixtures
git commit -m "mise à jour des fixtures"
```

## Générer des fixtures pour les acteurs et propositions de service

Le volume de données de la table des Acteurs étant gigantesque, les fixtures de cette table sont générées manuellement, lorsque le modèle de données évolue et empêche leur installation ou lorsqu'il est nécessaire d'ajouter des données de test pour couvrir plus exhaustivement le contexte d'utilisation réel de l'application.

Pour ce faire, sont listées dans le `Makefile` une liste de `pk` d'acteurs (champ `identifiant_unique`).
Ces identifiants ont été récupérés à la main, depuis le frontend de la carte :

1. Faire une recherche pour la zone souhaitée
2. Récupérer le lien de l'acteur dans la fiche détaillée (en cliquant sur le lien de partage par exemple) --> https://quefairedemesdechets.ademe.fr/adresse_details/3kQK86DEWA3ZrcirdzzBez l'id est 3kQK86DEWA3ZrcirdzzBez
3. Chercher cet id dans l'admin Django : https://quefairedemesdechets.ademe.fr/admin/qfdmo/displayedacteur/?q=eYKxBYDMDoMXTr8iiw69Ek
4. Récupérer le champ `identifiant_unique` : il peut être un uuid ou un assemblage de chaînes de caractères mentionnant la source, par exemple `ocad3e_SGS-02069`
5. Ajouter cet identifiant dans le `Makefile` à la suite des autres, derrière le flag `--pk` dans la commande `generate-fixtures-acteurs`

6. Une fois cela fait, il faut récupérer les _primary key_ des propositions de service associées.
   Cela peut-être fait depuis le shell `django` :

```sh
make shell
```

```py
# 1. importer le modèle Django
from qfdmo.models import DisplayedActeur

# 2. Stocker les pks dans une variable. Les pks peuvent être copiées-collées depuis le Makefile
pks = ["uuid-dun-acteur", "identifiant-dun-autre-acteur"]

# 3. Filtrer les acteurs par pks et en récupérer les pks de propositions de services associées
list(DisplayedActeur.objects.filter(pk__in=pks).values_list("proposition_services__pk", flat=True))

# Sortie attendue: [2163243, 2163244, 2163245, 243160, 435885, 1699381, 738371, 738372, 719100]
```

7. Cette liste de `pk` peut alors être collées dans le `Makefile`
8. Les fixtures peuvent être re-générées

```sh
make generate-fixtures-acteurs

# il est conseillé de conserver dans git les fixtures à jour, et d'embarquer
# ces mises à jour dans les pull request.
git add qfdmo/fixtures
git commit -m "mise à jour des fixtures"
```

## Utiliser les fixtures

Les fixtures peuvent être utilisées de plusieurs manières :

- Dans les tests
- En local
- Dans la CI

En local, on utilise généralement une base de production mais il peut être intéressant d'installer les fixtures afin d'avoir un environnement _iso-CI_.
Pour ce faire :

```sh
# ⚠️ Cette commande va supprimer les données locales, elle est donc à executer en conscience
make db-restore-local-for-tests
```

Dans les tests, les fixtures peuvent être importées en utilisant la fonction `callcommand` de Django :

```py
from django.core.management import call_command
call_command('loaddata', 'synonymes', 'produits')
```

Le nom des fixtures à utiliser est celui du nom du fichier `.json` de la fixture.
Django se charge de découvrir automatiquement la fixture correspondante.

[^1]: [https://docs.djangoproject.com/en/5.2/topics/db/fixtures/](https://docs.djangoproject.com/en/5.2/topics/db/fixtures/)

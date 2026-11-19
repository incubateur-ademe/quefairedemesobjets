# Utiliser les fixtures

Le projet utilise des fixtures Django[^1] pour les tests.
Celles-ci sont basées sur de la donnée issue de la base de production afin de tester l'application sur des situations _de la vraie vie_.

## Générer des fixtures, cas général

Les fixtures peuvent être générées à partir d'une commande `make`. Il n'y a pas de fixtures d'acteurs : les tests end-to-end utilisent la base d'échantillon, cf. [create_webapp_sample_db.md](create_webapp_sample_db.md).

```sh
make generate-fixtures

# il est conseillé de conserver dans git les fixtures à jour, et d'embarquer
# ces mises à jour dans les pull request.
git add qfdmo/fixtures qfdmd/fixtures
git commit -m "mise à jour des fixtures"
```

## Utiliser les fixtures

Dans les tests, les fixtures peuvent être importées en utilisant la fonction `callcommand` de Django :

```py
from django.core.management import call_command
call_command('loaddata', 'synonymes', 'produits')
```

Le nom des fixtures à utiliser est celui du nom du fichier `.json` de la fixture.
Django se charge de découvrir automatiquement la fixture correspondante.

[^1]: [https://docs.djangoproject.com/en/5.2/topics/db/fixtures/](https://docs.djangoproject.com/en/5.2/topics/db/fixtures/)

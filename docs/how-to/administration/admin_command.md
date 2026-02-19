# Commandes Django d'administration

## Correction de la valeur d'un champs sur toute la base d'acteur

Cas d'utilisation : quand un groupe d'acteur conséquent a une valeur fausse et qu'on souhaite la corriger en masse.

Étape du script :

- Recherche la valeur à corriger parmis tous les acteurs compilés (VueActeur)
- Créer une révision si elle n'existe pas pour chaque acteur à corriger
- modifie la valeur du champ de la révision pour chaque acteur à corriger

Note: il existe une option `--dry-run` permettant de visualiser la correction avant de l'appliquer

```sh
(uv run) python manage.py correction_acteur_field --field champ_a_modifier --old_value "valeur à corriger" --new_value "Remplacer par cette valeur" (--dry-run)
```

ex d'utilisation

```sh
uv run python manage.py correction_acteur_field --field horaires_osm --old_value "Mo off; Tu off; We off; Th off; Fr off; Sa off; Su off" --new_value __empty__ --dry-run
```

## Population des propositions de service avec une sous-catégorie

Ajout d'une sous-catégorie aux propositions de service qui en contient une autre

Cette commande est utile quand on ajoute une nouvelle sous-catégorie car on a besoin de plus de détails, on veut alors pouvoir ajouter cette nouvelle sous-catégorie en masse aux propositions de service qui en contient une sous-catégorie spécifique.

```sh
(uv run) python manage.py populate_propositionservice --new_sous_categorie_code sous_categorie_a_populer --origin_sous_categorie_code sous_categorie_pour_identifier_les_propositions_de_service_a_populer (--dry-run)
```

Par exemple : on souhaite ajouter la sous-catégorie "Poêle et Casserole" aux propositions de service qui en contiennent la sous-catégorie "Vaisselle"

```sh
uv run python manage.py populate_propositionservice --new_sous_categorie_code poele_casserole --origin_sous_categorie_code vaisselle --dry-run
```

# Commandes Django d'administration

## Correction de la valeur d'un champs sur toute la base d'acteur

Cas d'utilisation : quand un group d'acteur conséquent a une valeur fausse et qu'on souhaite la corriger en masse.

Etape du script :

- Recherche la valeur à corriger parmis tous les acteurs compilés (VueActeur)
- Créer une révision si elle n'existe pas pour l'acteur
- modifie la valeur du champ de la révision

Note: il existe une option `--dry-run` permettant de visualiser la correction avant de l'appliquer

```sh
(uv run) python manage.py correction_acteur_field --field champ_a_modifier --old_value "valeur à corriger" --new_value "Remplacer par cette valeur" (--dry-run)
```

ex d'utilisation

```sh
uv run python manage.py correction_acteur_field --field horaires_osm --old_value "Mo off; Tu off; We off; Th off; Fr off; Sa off; Su off" --new_value __empty__ --dry-run
```

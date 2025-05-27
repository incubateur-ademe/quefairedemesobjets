# Utilisation des contraintes SQL

On utilise les contraintes SQL pour imposer des critères de qualité à la donnée. Ces contraintes sont à mettre en oeuvre via les modèles Django (option [Meta.constraints](https://docs.djangoproject.com/en/5.1/ref/models/options/#django.db.models.Options.constraints)). Voir [proposition initiale](https://github.com/incubateur-ademe/quefairedemesobjets/pull/1227).

## Contraintes conditionnelles

On utilise aussi des contraintes conditionnelles, par exemple, l'unicité du couple (`source_id`, `identifiant_externe`) pour les acteurs `actif` uniquement.

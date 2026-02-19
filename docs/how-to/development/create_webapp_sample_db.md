# Création de la base de données webapp_sample pour les tests

La base de données `webapp_sample` est une base de données généré en preprod dont on utilise le backup pour créer une base de tests.
Elle permet de disposer d'un environnement de test isolé avec un échatillon de données d'acteurs à afficher sans impacter la base de données principale.

Dans le cas de développement/debuggage de cette fonctionnalité, on a besoin de cette base de données configurée localement.

## Création de la base de données

Pour créer la base de données `webapp_sample` localement, utilisez la commande Django suivante :

```sh
uv run python manage.py create_webapp_sample_db
```

Cette commande effectue automatiquement :

1. **Création de la base de données** `webapp_sample` si elle n'existe pas déjà
2. **Création de l'utilisateur** `webapp_sample` avec les permissions nécessaires (superuser)
3. **Configuration des extensions PostgreSQL** requises (postgis, pg_stat_statements, unaccent, pg_trgm, uuid-ossp, postgres_fdw)

Si la base de données existe déjà, la commande affichera un avertissement mais continuera l'exécution pour s'assurer que les permissions et extensions sont correctement configurées.

## Configuration

La base de données `webapp_sample` est configurée dans `webapp/core/settings.py` en utilisant la variable d'environnement `DB_WEBAPP_SAMPLE`

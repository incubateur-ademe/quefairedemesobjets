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

## Restaurer la base de données depuis une base distante

Pour peupler la base de données `webapp_sample` locale à partir d'une base distante (ex : preprod), utilisez le script :

```sh
make db-restore-local-from-sample
```

Ce script effectue automatiquement :

1. **Dump** de la base distante via `pg_dump`
2. **Suppression et recréation** du schéma `public` local
3. **Création des extensions** PostgreSQL requises
4. **Restauration** du dump dans la base locale
5. **Suppression** du fichier de dump temporaire

### Variables d'environnement requises

| Variable                     | Description                                                 |
| ---------------------------- | ----------------------------------------------------------- |
| `REMOTE_SAMPLE_DATABASE_URL` | URL de connexion à la base distante à copier (ex : preprod) |
| `SAMPLE_DATABASE_URL`        | URL de connexion à la base locale cible                     |

Ces deux variables doivent être définies dans le fichier `.env` (voir `.env.template`).

`REMOTE_SAMPLE_DATABASE_URL` doit pointer vers une base accessible depuis votre machine.

## Configuration

La base de données `webapp_sample` est configurée dans `webapp/core/settings.py` en utilisant la variable d'environnement `DB_WEBAPP_SAMPLE`

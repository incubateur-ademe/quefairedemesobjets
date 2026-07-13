# Django

## Applications

- `core` : main access point, handle shared code
- `qfdmo` : handle map and acteur
- `qfdmd` : handle advise about circular economy
- `search` : search engine
- `data` : object used by the backoffice to handle data
- `infotri` : info tri widget
- `stats` : stats api
- `dsfr-hacks` : tooling to help about using DSFR

### Django Tips

- Use class-based views when appropriate
- Prefer `LoginRequiredMixin` for protected views
- use Mixin classes to handle shared behaviour
- Use `prefetch_related` and `select_related` to optimize queries

## Tâches asynchrones (django-tasks)

Certaines actions du back-office Django Admin — notamment l'application en masse de suggestions sur les `SuggestionGroupe` — peuvent traiter des milliers d'enregistrements. Pour éviter les timeouts HTTP, ces actions passent par **[django-tasks](https://github.com/RealOrangeOne/django-tasks)** avec un backend PostgreSQL (`django_tasks.backends.database.DatabaseBackend`).

### Architecture

| Composant                           | Rôle                                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Tâches** (`webapp/data/tasks.py`) | Fonctions décorées avec `@task()` ; exécutées hors requête HTTP.                               |
| **File d'attente**                  | Tables Django créées par `django_tasks.backends.database` dans la DB webapp (`DATABASE_URL`).  |
| **Worker**                          | Processus dédié `python manage.py db_worker` qui consomme la file.                             |
| **Processus web**                   | Gunicorn / `runserver` — enqueue les tâches ou les exécute de façon synchrone selon le volume. |

### Seuil synchrone / asynchrone

Les actions admin `[SOURCE] Appliquer les suggestions au parent` et `[SOURCE] Appliquer les suggestions à la correction de l'acteur` (`webapp/data/admin.py`) choisissent le mode d'exécution selon le nombre de `SuggestionGroupe` sélectionnés :

| Sélection   | Comportement                                                                                                                                         |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **< 1 000** | Exécution **synchrone** via `task.call(ids)` dans le processus web. L'utilisateur voit le résultat immédiatement.                                    |
| **≥ 1 000** | Exécution **asynchrone** via `task.enqueue(ids)`. L'utilisateur est informé que le traitement est lancé en arrière-plan ; le worker prend le relais. |

Le seuil est défini par la constante `SUGGESTION_TASK_ASYNC_THRESHOLD` dans `webapp/data/admin.py`.

### Développement local

Depuis `webapp/` :

```sh
make runserver
```

La cible `runserver` du Makefile lance **`db_worker` en arrière-plan** puis `runserver`. Sans worker, les actions asynchrones (≥ 1 000 entrées) resteraient en file d'attente.

Pour lancer le worker seul (par exemple après un `runserver` démarré autrement) :

```sh
uv run python manage.py db_worker
```

Les tests utilisent le backend `ImmediateBackend` (`webapp/settings/test.py`) : les tâches s'exécutent inline, sans worker.

### Production (Scalingo)

Le `Procfile` déclare deux types de processus :

```text
web: bash bin/start
worker: python manage.py db_worker
postdeploy: bash bin/post_deploy
```

Scalingo démarre un container **`worker`** distinct du container **`web`**. Les deux partagent la même `DATABASE_URL` : le web enqueue, le worker consomme.

Voir aussi [`infrastructure/provisioning.md`](../infrastructure/provisioning.md) pour le détail du déploiement.

### Ajouter une nouvelle tâche

1. Déclarer la fonction dans le module `tasks.py` de l'app concernée avec `@task()`.
2. Passer des **identifiants sérialisables** (listes d'IDs, pas de queryset) : la tâche peut s'exécuter dans un autre processus et doit re-fetcher les objets.
3. Depuis une vue ou une action admin, appeler `.call(...)` pour une exécution synchrone ou `.enqueue(...)` pour la mettre en file.
4. Tester avec `ImmediateBackend` ; vérifier localement avec `db_worker` si la tâche est destinée à être enqueueée.

# Installation de l'application en local

## Environnement de développement

### Prérequis

- Docker et Docker Compose : c'est le seul prérequis pour lancer l'application. Python, Node, GDAL et Postgres tournent dans les conteneurs, aux mêmes versions qu'en CI et en production.

Optionnel, selon ce que vous faites :

- node 24 sur la machine, pour lancer les tests end-to-end Playwright (`mise` ou `asdf` lisent `.tool-versions`)
- [uv](https://docs.astral.sh/uv/) sur la machine, pour les hooks de pre-commit et l'autocomplétion de l'éditeur
- Le client Scaleway, en suivant [les instructions de Scaleway](https://www.scaleway.com/en/docs/scaleway-cli/quickstart/), pour copier la base de production
- Le client Scalingo, en suivant [les instructions de Scalingo](https://doc.scalingo.com/platform/cli/start)
- [OpenTofu](https://opentofu.org/docs/intro/install/) et [Terragrunt](https://terragrunt.gruntwork.io/docs/getting-started/install/), pour l'infrastructure

### Technologies

Cette liste est non-exhaustive.

Webapp:

- Python
- Django
- Node
- Typescript
- Parcel
- DSFR
- Honcho
- Whitnoise
- Tailwind
- nginx

Plateforme data :

- Airflow
- DBT

CI/CD:

- Github
- Dependabot

Administration:

- Scalingo
- Scaleway
- Sentry

Dev tools:

- Pytest
- Playwright
- Django-debug-toolbar

Provisionnement:

- OpenTofu
- Terragrunt

## Installation rapide

```sh
make setup
```

Cette commande construit les images, démarre la stack, applique les migrations et crée un superutilisateur d'exemple (`admin` / `admin`). Elle peut être relancée sans risque. La base est vide après une première installation.

L'application est ensuite accessible sur [http://quefairedemesdechets.localhost](http://quefairedemesdechets.localhost) (derrière nginx, comme en production) ou sur [http://localhost:8000](http://localhost:8000) (Django directement). Les domaines en `.localhost` pointent sur la machine sans modifier `/etc/hosts`.

Pour la peupler, cf. [Copier la base de données de prod en local](useful_command.md#copier-la-base-de-donnees-de-prod-en-local).

## Services Docker Compose

| Service     | Rôle                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------ |
| `webapp`    | Django : migrations au démarrage, puis `runserver` (port 8000)                                   |
| `worker`    | `db_worker`, qui traite les tâches de fond (django-tasks), par exemple les actions admin lourdes |
| `assets`    | `npm ci` si `package-lock.json` a changé, puis `parcel watch`                                    |
| `proxy`     | nginx local, avec la même configuration que la production (port 80)                              |
| `webapp-db` | PostGIS (port 6543 sur la machine)                                                               |

Le profile `airflow` ajoute `warehouse-db` (8765), `airflow-db` (7654), `airflow-webserver` (8080), `airflow-scheduler` (12 G RAM) et `airflow-dag-processor` (8082).

> Pas de **Redis** ni de **mailcatcher** en local : le cache Django est stocké en base (`django.core.cache.backends.db.DatabaseCache`, table `qf_django_cache`).

## Commandes du quotidien

```sh
make up                       # démarrer, après un git pull par exemple
make down                     # arrêter
make logs                     # suivre les logs
make add pkg=requests         # ajouter une dépendance Python (group=dev pour un groupe)
make add-js pkg=lodash        # ajouter une dépendance JavaScript
make -C webapp shell          # shell Django
make -C webapp makemigrations
make -C webapp createsuperuser
```

Les cibles de `webapp/Makefile` s'exécutent dans les conteneurs. `make DOCKER= NPM_DOCKER= <cible>` les exécute sur la machine, ce qui suppose d'y avoir installé Python, Node et GDAL : ce mode n'est pas maintenu.

### Versions de Python, Node et uv

`.tool-versions`, à la racine, est le seul endroit où elles sont écrites. `make` les lit et les passe à la construction des images, la CI fait de même. Les images se construisent donc avec `make up`, pas avec `docker compose build` seul.

Pour changer de version : modifier `.tool-versions` (et `.python-version`, lu par Scalingo et uv, que la CI vérifie identique), puis `make up`.

### Dépendances à jour

`make up` reconstruit les images quand `uv.lock`, `package-lock.json` ou un Dockerfile a changé. En plus, à chaque démarrage, `webapp` resynchronise son virtualenv sur `uv.lock` et `assets` réinstalle `node_modules` si `package-lock.json` a changé. Un `git pull` qui apporte de nouvelles dépendances ou migrations est donc pris en compte par un simple `make up`.

## Variables d'environnement

Aucun fichier `.env` n'est nécessaire : `docker-compose.yml` porte les valeurs par défaut de tout ce qui n'est pas un secret, y compris les adresses des bases sur le réseau Docker.

Le fichier `.env` à la racine sert uniquement aux secrets et aux surcharges, cf. `.env.template`. Par exemple, pour travailler avec un autre Postgres que celui de Compose :

```sh
DATABASE_URL=postgres://user:password@host.docker.internal:5432/webapp # pragma: allowlist secret
```

`webapp/.env.template` reste utilisé par pytest et par les tests JS.

Si vous aviez une installation précédente : supprimez `webapp/.env`, et retirez du `.env` racine les adresses de base en `localhost` (`DATABASE_URL`, `DB_WEBAPP_SAMPLE`, `DB_WAREHOUSE`), qui ne sont pas joignables depuis les conteneurs.

## Tester l'application

Tests Python (pytest) et tests JS unitaires, depuis le dossier **`webapp/`** :

```sh
make unit-test
make integration-test
make js-test
```

End-to-end avec Playwright.
Ces tests nécessitent une base de données incluant un échantillon d'acteurs issus de la base de données principale.
Celle-ci peut être générée en local facilement, via une commande à lancer depuis la racine du dépôt.
(`make e2e-prepare` construit l'échantillon via le DAG `compute_sample_acteur`,
voir [create_webapp_sample_db.md](create_webapp_sample_db.md)) :

```sh
npm ci                          # Playwright tourne sur la machine
make -C webapp init-playwright
make e2e            # préparation + tests
```

Le navigateur tourne sur la machine, et Playwright démarre lui-même le serveur testé dans le service `webapp`, sur le port 8888.

Pour relancer seulement les tests (depuis **`webapp/`**) :

```sh
make e2e-test
make e2e-test-ui
```

Test d'accessibilité (depuis **`webapp/`**) :

```sh
make a11y
```

## Installer les hooks de pre-commit

Les hooks tournent sur la machine, avec uv :

```sh
uv sync --group dev
uv run pre-commit install
```

## Installation de la plateforme DATA

Copier les variables d'environnement `data-platform/dags/.env.template` vers `data-platform/dags/.env` :

```sh
cp data-platform/dags/.env.template data-platform/dags/.env
```

Lancer les containers docker avec docker compose:

```sh
docker compose --profile airflow up
```

docker compose lancera :

- la base de données postgres nécessaire à la webapp de la carte
- la base de données postgres nécessaire à Airflow
- un webserver airflow
- un scheduler airflow en mode LocalExecutor

accéder à l'interface d'Airflow en local [http://localhost:8080](http://localhost:8080) ; identifiant/mot de passe : airflow / airflow

### Tester la plateforme Data

Tests Python des DAGs (pytest), depuis la racine du repo :

```sh
uv sync --group dev --group notebook
cd data-platform && make dags-test
```

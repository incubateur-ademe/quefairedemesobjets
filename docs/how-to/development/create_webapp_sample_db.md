# Créer la base d'échantillon `webapp_sample` pour les tests e2e

Les tests e2e tournent sur `webapp_sample`, une base réduite (~2 000 acteurs)
isolée de votre base de développement. Elle est construite **entièrement en
local** par le DAG Airflow `compute_sample_acteur`.

> Aucune base d'échantillon distante n'est copiée. L'ancienne variable
> `REMOTE_SAMPLE_DATABASE_URL` et le script `restore_sample_locally.sh` ont été
> supprimés : l'échantillon se régénère à partir de votre base `webapp` locale.

## En une commande

```sh
make e2e-prepare   # vérifie les prérequis, joue le DAG, prépare la webapp
make e2e           # idem puis lance les tests Playwright
```

`scripts/e2e_prepare.sh` s'arrête avec un message explicite si la base
`webapp` est vide (restaurer la prod d'abord) ; il crée le pont
`postgres_fdw` s'il manque.

## Le processus complet

```text
prod ──(1) restauration──► webapp ──(2) postgres_fdw──► warehouse
                             │                             │
                             │                       (3) dbt +tag:sample
                             │                             │
                             └──(4) copy_db_schema/data────►│
                                                            │
                                   (5) copy_displayed_data──► webapp_sample
```

### 1. Restaurer la production dans `webapp`

L'échantillon dérive de la base `webapp`, qui doit contenir des acteurs :

```sh
make db-restore-local-from-prod
```

### 2. Créer le pont `postgres_fdw`

`warehouse` lit `webapp` via le schéma virtuel `webapp_public` :

```sh
make webapp-create-remote-db-server
```

Inclus dans la restauration prod, et rejoué au besoin par `make e2e-prepare`.

### 3 à 5. Jouer le DAG `compute_sample_acteur`

En CLI (ce que fait `make e2e-prepare`) :

```sh
./scripts/e2e_run_sample_dag.sh
```

Ou via l'UI Airflow sur <http://localhost:8080> (identifiants `airflow` /
`airflow`) : chercher **[TEST] Calculer l'échantillon des acteurs**, puis
_Trigger DAG_.

Les cinq tâches enchaînées :

| Tâche                                | Rôle                                                           |
| ------------------------------------ | -------------------------------------------------------------- |
| `dbt_run_base_acteurs`               | construit les modèles `+tag:sample` dans `warehouse`           |
| `dbt_test_base_acteurs`              | joue les tests dbt sur ces modèles                             |
| `copy_db_schema`                     | copie le schéma `webapp` → `webapp_sample`                     |
| `copy_db_data`                       | copie les données de référence `webapp` → `webapp_sample`      |
| `copy_displayed_data_from_warehouse` | copie les acteurs échantillonnés `warehouse` → `webapp_sample` |

Le sélecteur dbt est `+tag:sample` : le préfixe `+` inclut les modèles amont
(`base_displayedacteur`, `base_epci`, `base_acteur_type`…). Sans lui, sur un
warehouse vierge, dbt échoue sur
`relation "public.base_displayedacteur" does not exist`.

## Contenu de l'échantillon

Défini par `models/exposure/acteurs/sample/exposure_sample_displayedacteur.sql` :

- EPCI **Auray Quiberon Terre Atlantique** (`200043123`)
- EPCI **Pays de Montbéliard Agglomération** (`200065647`)
- tous les acteurs de type `acteur_digital`

Les tests e2e s'appuient sur ce périmètre (recherches sur Auray notamment).

## Créer la base seule

Pour repartir d'une base `webapp_sample` vide (rôle, extensions, config de
recherche `wagtail_french`) sans jouer le DAG :

```sh
cd webapp && uv run python manage.py create_webapp_sample_db
```

## En CI

La CI ne dispose pas de stack Airflow : elle restaure un dump de la base
d'échantillon de preprod via le secret `SAMPLE_DB_URI`
(`.github/actions/prepare-django-db`). Ce chemin distant ne concerne que la CI ;
en local, l'échantillon est toujours reconstruit par le DAG.

## Configuration

La connexion est définie par `DB_WEBAPP_SAMPLE` (voir `webapp/.env.template`)
et consommée dans `webapp/settings/base.py` ainsi que par
`webapp/playwright.config.ts`, qui la passe en `DATABASE_URL` au serveur de
test.

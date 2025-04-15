# Development

## Environnement de développement

### Prérequis

- docker-compose
- python 3.12
- node 20
- gdal (librairie nécessaire à l'utilisation de GeoDjango)

Conseil: utiliser `asdf` pour la gestion des environnement virtuel `node` et `python`

#### Spécificité d'installation pour les processeur Mx de Mac

[https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e](https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e)

### Technologies

- Python
- Django
- DBT
- github
- Licence MIT
- Node
- Parcel
- DSFR
- honcho
- Scalingo
- Sentry
- Pytest
- Whitnoise
- Tailwind
- Dependabot
- Django-debug-toolbar

### Installation & Exécution

Configuration des variables d'environnement: ajouter (ou mettre à jour si existant)
la variable AIRFLOW_UID de telle sorte à ce que Docker lance Airflow avec notre utilisateur

```sh
cp .env.template .env
sed -i '/^AIRFLOW_UID=/d' .env && echo "AIRFLOW_UID=$(id -u)" >> .env
```

Modifier les variables dans le fichier .env si nécessaire

Les bases de données source `MySQL` et cible `Postgres + Postgis` sont executées et mises à disposition par le gestionnaire de conteneur Docker

```sh
docker compose  --profile lvao up
```

Installation des dépendances python et javascript

```sh
poetry env activate
poetry install --with dev,airflow
npm install
```

Migration

```sh
python manage.py migrate
```

Population de la base (optionel, si la base de données de production est chargée sur l'environnement de développement)

```sh
python manage.py loaddata categories actions acteur_services acteur_types
```

### Create superuser

```sh
python manage.py createsuperuser
```

### Lancement

```sh
docker compose --profile airflow up -d
honcho start -f Procfile.dev
```

Honcho démarrera les containers Docker s'ils ne sont pas déjà démarrés.
Une fois les processus démarrés, le serveur web sera accessible à l'adresse http://localhost:8000, écoutant sur le port 8000.

### Test

Test python avec pytest

```sh
pytest
```

Test Js unitaire

```sh
npm run test
```

End to end avec Playwright

```sh
npx playwright install --with-deps
npx playwright test
```

### Ajout et modification de package

#### Python

Utiliser poetry

```sh
poetry add <package>
```

option `--group dev` pour les dépendances de développement et `--group airflow` pour les dépendances de airflow

#### Javascript

Utiliser npm

```sh
npm install <package>
```

option `--dev` pour les dépendances de développement

### Installer les hooks de pre-commit

Pour installer les git hook de pre-commit, installer le package precommit et installer les hooks en executant pre-commit

```sh
pre-commit install
```

### populate Acteur Réemploi from LVAO Base file

Create a one-off contanier and download LVAO base file from your local using --file option.

```sh
scalingo --region osc-fr1 --app quefairedemesobjets run --file backup_db.bak/Base_20221218_Depart.csv bash
```

following message should be display in prompt:

```txt
-----> Starting container one-off-1576  Done in 0.224 seconds
 Upload /Users/nicolasoudard/workspace/beta.gouv.fr/quefairedemesobjets/backup_db.bak/Base_20221218_Depart.csv to container.
…
```

uploaded file is stored in `/tmp/uploads` folder

Launch import :

```sh
python manage.py populate_lvao_base /tmp/uploads/Base_20221218_Depart.csv
```

### Import DB from production

```bash
DUMP_FILE=</path/to/dump/file.pgsql>
DATABASE_URL=postgres://qfdmo:qfdmo@localhost:6543/qfdmo  # pragma: allowlist secret

for table in $(psql "${DATABASE_URL}" -t -c "SELECT \"tablename\" FROM pg_tables WHERE schemaname='public'"); do
     psql "${DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;"
done
pg_restore -d "${DATABASE_URL}" --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}"
```


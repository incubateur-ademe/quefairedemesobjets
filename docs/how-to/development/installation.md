# Installation de l'application en local

## Environnement de développement

### Prérequis

- docker & docker-compose
- python 3.12
- node 20
- mkcert (optionnel : utilisé pour la génération de certificats pour le développement frontend de la carte et assistant)
- gdal (librairie nécessaire à l'utilisation de GeoDjango)
- Installer et configurer le client Scaleway en suivant [les instructions de Scaleway](https://www.scaleway.com/en/docs/scaleway-cli/quickstart/)
- Installer et configurer le client Scalingo en suivant [les instructions de Scalingo](https://doc.scalingo.com/platform/cli/start)
- [OpenTofu](https://opentofu.org/docs/intro/install/) et [Terragrunt](https://terragrunt.gruntwork.io/docs/getting-started/install/)

Conseil: utiliser `asdf` ou `mise` pour la gestion des environnements virtuel `node` et `python`

⚠️ L'accès à la plateforme Scaleway est nécessaire pour exécuter la copie de la base de données de production en local

#### Spécificité d'installation pour les processeurs Mx de Mac

[https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e](https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e)

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

la commande `init-dev` installe tout l'environnement Webapp et plateforme data

```sh
make init-dev
```

### Lancement de la webapp et de la plateforme data

Modifier le fichier `/etc/hosts`, ajouter les lignes

```
127.0.0.1       lvao.ademe.local
127.0.0.1       quefairedemesdechets.ademe.local
127.0.0.1       quefairedemesobjets.ademe.local
```

Copier la base de données de prod

```sh
make db-restore-local-from-prod
```

Lancer l'application

```sh
make run-all
```

la webapp est accessible à l'adresse [quefairedemesobjets.ademe.local](https://quefairedemesobjets.ademe.local/)
la plateforme data est accessible à l'adresse [http://localhost:8080](http://localhost:8080)

## Installation de la Webapp uniquement

### Configuration

Modifier le fichier `/etc/hosts`, ajouter les lignes

```
127.0.0.1       lvao.ademe.local
127.0.0.1       quefairedemesdechets.ademe.local
127.0.0.1       quefairedemesobjets.ademe.local
```

### Installation & Exécution

Configuration des variables d'environnement: ajouter (ou mettre à jour si existant)

```sh
cp .env.template .env
```

Modifier les variables dans le fichier .env si nécessaire

Générer les certificats utilisé par nginx

make init-certs

Les bases de données `Postgres + Postgis` sont executées et mises à disposition par le gestionnaire de conteneur Docker

Pour lancer uniquement les services utiliser par la webapp

```sh
docker compose  --profile lvao up -d
```

Installation des dépendances python et javascript

```sh
uv env activate
uv sync --all-packages
npm ci
```

Migration

```sh
python manage.py migrate
```

Créer la table de cache

```sh
make createcachetable
```

Pour peupler la base de données `webapp` le plus simple est de copier la base de données de production, cf. [Copier la base de données de prod en local](useful_command.md#copier-la-base-de-donnees-de-prod-en-local)

Sinon, utiliser la command de peuplement ci-dessous

```sh
make seed-database
```

### Créer un superutilisatteur

Si vous n'en avez pas déjà un

```sh
python manage.py createsuperuser
```

### Lancement

```sh
make run-django
```

Honcho démarrera les containers Docker s'ils ne sont pas déjà démarrés.
Une fois les processus démarrés, le serveur web sera accessible à l'adresse [quefairedemesobjets.ademe.local](https://quefairedemesobjets.ademe.local/), écoutant sur le port 8000.

### Tester l'application

Test python avec pytest

```sh
make unit-test
make integration-test
```

Test Js unitaire (DEPRECATED ?)

```sh
npm run test
```

End to end avec Playwright

```sh
make init-playwright
make e2e-test
make e2e-test-ui
```

Test d'accessibilité

```sh
make a11y
```

### Installer les hooks de pre-commit

Pour installer les git hook de pre-commit, installer le package precommit et installer les hooks en executant pre-commit

```sh
pre-commit install
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

Test python avec pytest

```sh
make dags-test
```

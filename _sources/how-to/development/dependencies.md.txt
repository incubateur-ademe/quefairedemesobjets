# Gestion de package

## Dépendances Python

On utilise **uv** avec **deux projets distincts** :

- **`webapp/`** : application Django (fichiers `webapp/pyproject.toml` et `webapp/uv.lock`)
- **`data-platform/`** : DAGs Airflow, dbt, etc. (`data-platform/pyproject.toml` et `data-platform/uv.lock`)

Pour installer les paquets en local, aller dans le dossier du projet concerné :

```sh
cd webapp && uv sync <package>
cd data-platform && uv sync <package>
```

Pour ajouter une dépendance (toujours depuis le bon dossier) :

```sh
uv add <package>
```

Option `--group dev` pour les dépendances de développement (pytest, ruff, etc.).

## Dépendances Javascript

Utiliser npm

```sh
npm install <package> --before="$(date -v -7d +%Y-%m-%d)" # testé sur MacOS et Debian
```

option `--dev` pour les dépendances de développement
Note : on recommande un cooldown de 7 jours pour les nouvelles dépendances afin de se prémunir des supply chain attacks.

# Gestion de package

## Dépendances Python

On utilise uv

Pour installer les packages en local

```sh
uv sync <package>
```

Pour ajouter une dépendance

```sh
uv add <package>
```

option `--group dev` pour les dépendances de développement et `--group airflow` pour les dépendances de airflow

## Dépendances Javascript

Utiliser npm

```sh
npm install <package>
```

option `--dev` pour les dépendances de développement

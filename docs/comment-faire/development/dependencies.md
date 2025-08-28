# Gestion de package

## Dépendances Python

On utilise poetry

Pour installer les packages en local

```sh
poetry sync <package>
```

Pour ajouter une dépendance

```sh
poetry add <package>
```

option `--group dev` pour les dépendances de développement et `--group airflow` pour les dépendances de airflow

## Dépendances Javascript

Utiliser npm

```sh
npm install <package>
```

option `--dev` pour les dépendances de développement

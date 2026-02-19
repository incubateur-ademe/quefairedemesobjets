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
npm install <package> --before="$(date -v -7d +%Y-%m-%d)" # testé sur MacOS et Debian
```

option `--dev` pour les dépendances de développement
Note : on recommande un cooldown de 7 jours pour les nouvelles dépendances afin de se prémunir des supply chain attacks.

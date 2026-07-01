# Gestion de package

## Dépendances Python

On utilise **uv** avec un **workspace unique** à la racine du repo (un seul `uv.lock`).

Dépendances de production : chaque membre (`webapp/`, `data-platform/`) déclare les siennes dans son propre `pyproject.toml`.

Dépendances de développement : toutes centralisées dans le `pyproject.toml` racine, réparties en groupes sémantiques :

| Groupe       | Contenu                                                            | Usage                   |
| ------------ | ------------------------------------------------------------------ | ----------------------- |
| `lint`       | black, ruff                                                        | CI linter, pre-commit   |
| `test`       | pytest*, factory-boy                                               | CI tests                |
| `dev`        | lint + test + djade + pre-commit                                   | CI + dev de base        |
| `webapp-dev` | django-browser-reload, debug-toolbar, silk, honcho, ptpython, etc. | Développement webapp    |
| `notebook`   | dedupe, ipython                                                    | Notebooks data-platform |

Pour installer en local (depuis la racine du repo) :

```sh
uv sync --all-groups   # tout installer
uv sync --group dev    # minimum pour les tests
```

Pour ajouter une dépendance :

```sh
uv add --package webapp-quefairedemesobjetsetdechets <package>
uv add --package data-platform <package>
```

Pour ajouter une dépendance de développement (au workspace root) :

```sh
uv add --group lint <package>
uv add --group dev <package>
```

## Dépendances Javascript

Utiliser npm

```sh
npm install <package> --before="$(date -v -7d +%Y-%m-%d)" # testé sur MacOS et Debian
```

option `--dev` pour les dépendances de développement
Note : on recommande un cooldown de 7 jours pour les nouvelles dépendances afin de se prémunir des supply chain attacks.

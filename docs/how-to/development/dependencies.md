# Gestion de package

## Dépendances Python

On utilise **uv** avec un **workspace unique** à la racine du repo (un seul `uv.lock`).

Dépendances de production : chaque membre (`webapp/`, `data-platform/`) déclare les siennes dans son propre `pyproject.toml`. Le projet racine dépend du membre webapp pour que le buildpack Scalingo (`uv sync --locked --no-default-groups`) installe uniquement la webapp.

Dépendances de développement : toutes centralisées dans le `pyproject.toml` racine, réparties en groupes sémantiques :

| Groupe       | Contenu                                                    | Usage                   |
| ------------ | ---------------------------------------------------------- | ----------------------- |
| `lint`       | black, ruff                                                | CI linter, pre-commit   |
| `test`       | pytest*, factory-boy                                       | CI tests                |
| `dev`        | lint + test + djade + pre-commit                           | CI + dev de base        |
| `webapp-dev` | django-browser-reload, debug-toolbar, silk, ptpython, etc. | Développement webapp    |
| `notebook`   | dedupe, ipython                                            | Notebooks data-platform |

Pour installer en local (depuis la racine du repo) :

```sh
uv sync --all-packages --all-groups   # tout installer (webapp + data-platform + groupes)
uv sync --group dev                   # webapp + groupe dev (défaut Scalingo-compatible)
uv sync --all-packages --group dev    # webapp + data-platform + groupe dev (tests CI)
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

### Déploiement Scalingo (webapp)

Le déploiement se fait **depuis la racine du monorepo** (pas de `PROJECT_DIR`). Le buildpack Python voit le `uv.lock` racine et exécute `uv sync --locked --no-default-groups`, ce qui installe le membre webapp via la dépendance déclarée dans le `pyproject.toml` racine.

Le frontend est construit via le `package.json` racine (`npm --prefix webapp`). `data-platform/`, `docs/` et `infrastructure/` sont exclus du slug via [`.slugignore`](../../../.slugignore).

**Ops** : la variable d’environnement Scalingo `PROJECT_DIR` ne doit **pas** être définie sur les apps webapp (preprod/prod).

## Dépendances Javascript

Utiliser npm **depuis `webapp/`** :

```sh
cd webapp
npm install <package> --before="$(date -v -7d +%Y-%m-%d)" # testé sur MacOS et Debian
```

option `--dev` pour les dépendances de développement
Note : on recommande un cooldown de 7 jours pour les nouvelles dépendances afin de se prémunir des supply chain attacks.

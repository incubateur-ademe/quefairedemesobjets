# Longue vie aux objets

Longue vie aux objets propose des solutions pour promouvoir les gestes de consommation responsable:

- Mise à disposition d'une cartographie d'Acteurs du ré-emploi et de la réparation en France (disponible aussi via une iframe)
- Promotion des gestes de consommation responsable tels que le don, le partage local et la réparation

Le site "Longue vie aux objets" est disponible à l'URL : [https://longuevieauxobjets.ademe.fr/](https://longuevieauxobjets.ademe.fr/)

**Certaines pages disposent d'une page dédiée :
- [Frontend](./docs/Frontend.md)
- [Commandes utiles](./docs/Commands.md)
- [Coding guidelines](./docs/Coding-guidelines.md)
- [Organisations des fichiers dans dags](./docs/Organisations-des-fichiers-dans-dags.md)

## Afficher l'application dans une Iframe

il suffit d'ajouter le script js suivant:

```html
<script src="https://lvao.ademe.fr/static/iframe.js"
  data-max_width="800"
  data-direction="jai"
  data-first_dir="jai"
  data-action_list="preter|donner|reparer|echanger|mettreenlocation|revendre"
></script>
```

les paramètres de l'iframe sont passés dans le dataset : en tant qu'attribut préfixé par `data-`

Les paramètres disponibles pour customiser l'affichage de l'iframe sont:

- `data-direction`, option `jai` ou `jecherche`, par défaut l'option de direction « Je cherche » est active
- `data-first_dir`, option `jai` ou `jecherche`, par défaut l'option de direction « Je cherche » est affiché en premier dans la liste des options de direction
- `data-action_list`, liste des actions cochées selon la direction séparées par le caractère `|` :
  - pour la direction `jecherche` les actions possibles sont : `emprunter`, `echanger`, `louer`, `acheter`
  - pour la direction `jai` les actions possibles sont : `reparer`, `preter`, `donner`, `echanger`, `mettreenlocation`, `revendre`
  - si le paramètre `action_list` n'est pas renseigné ou est vide, toutes les actions éligibles à la direction sont cochées
- `data-max_width`, largeur maximum de l'iframe, la valeur par défaut est 800px
- `data-height`, hauteur allouée à l'iframe cette hauteur doit être de 700px minimum, la valeur par défaut est 100vh
- `data-iframe_attributes`, liste d'attributs au format JSON à ajouter à l'iframe

La hauteur et la largeur de l'iframe peuvent être exprimées dans toutes les unités interprétées par les navigateurs ex: px, %, vh, rem…

Voir l'exemple d'integration de l'iframe « Longue vie aux objets » dans une page html : [iframe.html](./iframe.html)

### Alternative d'intégration de l'application

Il est aussi possible d'intégrer directement l'iframe à votre site sans l'appel au script `iframe.js`. Dans ce cas, vous devrez passer les paramètres de l'iframe dans l'url (sans le préfix `data-`), configurer les appels à la librairie `iframe-resizer` et passer les bons attributs à l'iframe.

Vous trouverez un exemple d'intégration ici : [iframe_without_js.html](./iframe_without_js.html)

## Modèle de données

Chaque acteur du ré-emploi et recyclage expose des propositions de service associées à un geste et une liste de catégories d'objet.

### Base de données simplifiée

![Essentiel de la base de données de l'application « Longue vie aux objets »](./static/documentation_files/qdfmo-db.png)

### Objets d'administration en base de données

Certains objets de la base de données sont des objets d'administration qui n'ont pas vocation aest mis à jour régulièrement. Ci-dessous les populations de ces objets en date du 18 septembre 2023.

**Direction de l'action** (qfdmo_actiondirection):

Détenir ou chercher un objet

**Action** (qfdmo_action):

Quelle action souhaitez vous faire, Exemple : réparer un objet, acheter de seconde main…

**Catégorie / Sous-catégorie / Objet** (qfdmo_categorieobjet, qfdmo_souscategorieobjet)

Classification des objets

**Type de service** (qfdmo_acteurservice)

Type des services rendu par l'acteur, Exemple : Achat/revente entre particuliers, Location par un professionnel, Pièces détachées…

**Type d'acteur** (qfdmo_acteurtype)

Exemple : commerce, association, acteur digital…

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

Les bases de données source `MySQL` et cible `Postgres + Postgis` sont executées et mises à disposition par le gestionnaire de conteneur Docker

```sh
docker compose  --profile lvao up
```

Création de l'environnement virtuel de votre choix (préférence pour asdf)

```sh
python -m venv .venv --prompt $(basename $(pwd))
source  .venv/bin/activate
```

Installation

```sh
pip install -r requirements.txt -r dev-requirements.txt
npm install
```

// Modifier les variables dans le fichier .env si nécessaire

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
honcho start -f Procfile.dev
```

Honcho démarrera les containers Docker s'ils ne sont pas déjà démarrés.
Une fois les processus démarrés, le serveur web sera accessible à l'adresse http://localhost:8000, écoutant sur le port 8000.

### Test

python avec pytest

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

### Ajout et modification de package pip-tools

Ajouter les dépendances aux fichiers `requirements.in` et `dev-requirements.in`

Compiler les dépendances:

```sh
pip-compile dev-requirements.in --generate-hashes
pip-compile requirements.in --generate-hashes
```

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
DATABASE_URL=postgres://qfdmo:qfdmo@localhost:6543/qfdmo

for table in $(psql "${DATABASE_URL}" -t -c "SELECT \"tablename\" FROM pg_tables WHERE schemaname='public'"); do
     psql "${DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;"
done
pg_restore -d "${DATABASE_URL}" --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}"
```

## Déploiement sur Scalingo

Nous avons besoin d'installer GDAL comme c'est expliqué dans la doc suivante : [https://techilearned.com/configure-geodjango-in-scalingo/](https://techilearned.com/configure-geodjango-in-scalingo/) cf. [https://doc.scalingo.com/platform/app/app-with-gdal](https://doc.scalingo.com/platform/app/app-with-gdal)

le code est déployé en preprod lors de la mise à jour de la branche main

et en production quand il est tagué avec en respectant le format de version semantique vX.Y.Z

### Déploiement du code de l'interface

le code de l'interface est déployé sur le repo git de scalingo à conditions que les tests soit passés avec succès via Github

### Déploiement des dags Airflow sur s3

le code des dags Airflow est déployé sur le repo s3 de clevercloud à conditions que les tests soit passés avec succès via Github

## Schema simplifié de base de données

```mermaid
---
title: Schéma simplifié les acteurs
---

classDiagram
    class ActeurService {
        - id: int
        - code: str
        - libelle: str
        - actions: List[Action]
    }

    class ActeurType {
        - id: int
        - code: str
        - libelle: str
    }

    class Source {
        - id: int
        - code: str
        - libelle: str
        - afficher: bool
        - url: str
        - logo_file: str
    }

    class LabelQualite {
        - id: int
        - code: str
        - libelle: str
        - afficher: bool
        - bonus: bool
        - type_enseigne: bool
        - url: str
        - logo_file: str
    }

    class DisplayedActeur {
        - nom: str
        - description: str
        - identifiant_unique: str
        - acteur_type: ActeurType
        - adresse: str
        - adresse_complement: str
        - code_postal: str
        - ville: str
        - url: str
        - email: str
        - location: Point
        - telephone: str
        - nom_commercial: str
        - nom_officiel: str
        - labels: List[LabelQualite]
        - acteur_services: List[ActeurService]
        - siret: str
        - source: Source
        - identifiant_externe: str
        - statut: ActeurStatus
        - naf_principal: str
        - commentaires: str
        - cree_le: datetime
        - modifie_le: datetime
        - horaires_osm: str
        - horaires_description: str
        - public_accueilli: str
        - reprise: str
        - exclusivite_de_reprisereparation: bool
        - uniquement_sur_rdv: bool
    }

    class DisplayedPropositionService {
        - action: Action
        - sous_categories: List[SousCategorieObjet]
        - acteur: Acteur
    }

    class Action {
        - id: int
        - code: str
        - afficher: bool
        - description: str
        - directions: List[Direction]
        - order: int
        - couleur: str
        - icon: str
        - groupe_action: GroupeAction
    }

    class Direction {
        - id: int
        - code: str
        - libelle: str
        - order: int
    }

    class GroupeAction {
        - id: int
        - code: str
        - afficher: bool
        - description: str
        - order: int
        - couleur: str
        - icon: str
    }

    class CategorieObjet {
        - id: int
        - code: str
        - libelle: str
    }

    class SousCategorieObjet {
        - id: int
        - code: str
        - libelle: str
        - afficher: bool
        - categorie: CategorieObjet
    }

    class Objet {
        - id: int
        - code: str
        - libelle: str
        - sous_categorie: SousCategorieObjet
    }

    Direction --> Action
    DisplayedActeur --> DisplayedPropositionService
    DisplayedActeur <--> ActeurService
    ActeurType --> DisplayedActeur
    Source --> DisplayedActeur
    LabelQualite <--> DisplayedActeur
    DisplayedPropositionService <-- Action
    DisplayedPropositionService <--> SousCategorieObjet
    CategorieObjet --> SousCategorieObjet
    SousCategorieObjet --> Objet
    GroupeAction --> Action
```

```mermaid
---
title: Schéma simplifié des relations autour des acteurs
---

erDiagram
    Direction }|--|{ Action : n-m
    DisplayedActeur ||--|{ DisplayedPropositionService : un-n
    ActeurType ||--|{ DisplayedActeur : un-n
    Source ||--|{ DisplayedActeur : un-n
    Action ||--|{ DisplayedPropositionService : un-n
    ActeurService }|--|{ DisplayedActeur : un-n
    DisplayedPropositionService }|--|{ SousCategorieObjet : n-m

```

```mermaid
---
title: Schéma de l'application des corrections des acteurs
---

flowchart TB
    subgraph Acteur importé
        direction LR
        Acteur --> PropositionService
    end
    subgraph Acteur Corrigé
        direction LR
        CorrectionEquipeActeur --> CorrectionEquipePropositionService
    end
    subgraph Acteur Affiché
        direction LR
        DisplayedActeur --> DisplayedPropositionService
    end

    Acteur --> CorrectionEquipeActeur --> DisplayedActeur
    Acteur --> DisplayedActeur
    PropositionService --> CorrectionEquipePropositionService --> DisplayedPropositionService
    PropositionService --> DisplayedPropositionService
```

## Conventions de code - Utilisation des langues françaises et anglaises

Nous suivons les règles et standards de l'industrie que nous contrôlons à chaque commit et Pull Request grâce à des outils tel que `ruff` ou `eslint`.

Cependant, ce projet est développé et propulsé par l'État français et doit être utilisable et administrable simplement par le plus grand nombre. Nous appliquons donc une règle spécifique quant à l'utilisation de la langue française versus la langue anglaise, nous avons donc défini les cas d'utilisation de ces 2 langues.

### En Français

A l'attention des administrés, administrations, administrateurs, et l'équipe Longue vie aux objets

- Git/Github Les commits, les Pull Request
- La documentation dans les markdowns
- Les noms et les champs des tables en base de données

### En Anglais

Dans le code, à l'attention des équipes techniques

- les fonctions
- les noms de variables
- les commentaires dans le code

### Effets de bord acceptés

Certaines variables combinant un nom d'objet et un suffixe ou préfixe peuvent être en franglais

Ex :  `acteur_by_id`

## Data platform

Longue vie aux objets est aussi une `data platform` dont la documentation est dans [README.airflow.md](./README.airflow.md)

## Sécurité

### Politique de sécurité

consultable ici : [./SECURITY.md](./SECURITY.md)

### Monitoring de sécurité

Les applications maintenues par la startup sont monitorées par l'application Dashlord disponible ici : [https://dashlord.incubateur.ademe.fr/](https://dashlord.incubateur.ademe.fr/)

### Monitoring de code

les robots suivants sont configurés en CI pour inspecter le code :

- CodeQL : controle de qualité de code
- GitGuardian : detection de mot de passe
- Dependabot : mise à jour des dépendances (1 fois par semaine)
- ruff : respect des standard de code python
- prettier, black : formatage de code

### Monitoring applicatif

L'application est monitorée par l'[instance Sentry de beta.gouv.fr](https://sentry.incubateur.net/organizations/betagouv/projects/que-faire-de-mes-objets/?project=115)

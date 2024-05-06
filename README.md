# Longue vie aux objets

Longue vie aux objets propose des solutions pour promouvoir les gestes de consommation responsable:

- Mise à disposition d'une cartographie d'Acteurs du ré-emploi et de la réparation en France (disponible aussi via une iframe)
- Promotion des gestes de consommation responsable tels que le don, le partage local et la réparation

Le site "Longue vie aux objets" est disponible à l'URL : [https://longuevieauxobjets.ademe.fr/](https://longuevieauxobjets.ademe.fr/)

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

| nom       | libelle  |
| --------- | ------------ |
| jecherche | Je recherche |
| jai       | J'ai         |

**Action** (qfdmo_action):

| nom              | libelle | description        | directions       |
| ---------------- | ----------- | ------------------ | ---------------- |
| preter           | Prêter      | NULL               | jai              |
| reparer          | Réparer     | NULL               | jai              |
| mettreenlocation | Louer       | Mettre en location | jai              |
| echanger         | Èchanger    | NULL               | jai, jerecherche |
| acheter          | Acheter     | Acheter d'occasion | jerecherche      |
| revendre         | Vendre      | NULL               | jai              |
| donner           | Donner      | NULL               | jai              |
| louer            | Louer       | NULL               | jerecherche      |
| emprunter        | Emprunter   | NULL               | jerecherche      |

**Catégories/Sous-catégories** (qfdmo_categorieobjet, qfdmo_souscategorieobjet)

| Catégories                 | Sous-catégorie                   |
| -------------------------- |----------------------------------|
| Bijou, montre, horlogerie  | Bijou, montre, horlogerie        |
| Bricolage / Jardinage      | Outillage (bricolage/jardinage)  |
| Electroménager             | Gros électroménager (froid)      |
| Electroménager             | Gros électroménager (hors froid) |
| Electroménager             | Petit électroménager             |
| Equipements de loisir      | "Jardin (mobilier accessoires)"  |
| Equipements de loisir      | Autre matériel de sport          |
| Equipements de loisir      | Instruments de musique           |
| Equipements de loisir      | Jouets                           |
| Equipements de loisir      | Vélos                            |
| Image & son & Informatique | Autres équipements électroniques |
| Image & son & Informatique | Écrans                           |
| Image & son & Informatique | Hifi/vidéo (hors écrans)         |
| Image & son & Informatique | Matériel informatique            |
| Image & son & Informatique | Photo/ciné                       |
| Image & son & Informatique | Smartphones/tablettes/consoles   |
| Livres & Multimedia        | CD/DVD/jeux vidéo                |
| Livres & Multimedia        | Livres                           |
| Mobilier et décoration     | Décoration                       |
| Mobilier et décoration     | Luminaires                       |
| Mobilier et décoration     | Mobilier                         |
| Mobilier et décoration     | Vaisselle                        |
| Produits divers            | Matériel médical                 |
| Produits divers            | Puériculture                     |
| Vêtements & Accessoires    | Chaussures                       |
| Vêtements & Accessoires    | Linge de maison                  |
| Vêtements & Accessoires    | Maroquinerie                     |
| Vêtements & Accessoires    | Vêtements                        |

Cette liste est amenée à évoluer et est probablement non exhaustive

**Type de service** (qfdmo_acteurservice)

| nom                                    |
| -------------------------------------- |
| Achat, revente entre particuliers      |
| Achat, revente par un professionnel    |
| Atelier d'auto-réparation              |
| Collecte par une structure spécialisée |
| Depôt-vente                            |
| Don entre particuliers                 |
| Echanges entre particuliers            |
| Hub de partage                         |
| Location entre particuliers            |
| Location par un professionnel          |
| Partage entre particuliers             |
| Pièces détachées                       |
| Relai d'acteurs et d'événements        |
| Ressourcerie, recyclerie               |
| Service de réparation                  |
| Tutoriels et diagnostics en ligne      |

Cette liste est amenée à évoluer et est probablement non exhaustive

**Type d'acteur** (qfdmo_acteurtype)

| nom            | libelle                                                |
| -------------- | ---------------------------------------------------------- |
| acteur digital | Acteur digital (site web, app. mobile)                     |
| commerce       | Franchise, enseigne commerciale                            |
| artisan        | Artisan, commerce indépendant                              |
| collectivité   | Collectivité, établissement public                         |
| ess            | Association, entreprise de l'économie sociale et solidaire |

Cette liste est amenée à évoluer et est probablement non exhaustive

## Environnement de développement

### Prérequis

- docker-compose
- python 3.11
- node 18.17
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

Les bases de données source `MySQL` et cible `Postgres + Postgis` sont executées et mises à disposition par le gestionnaire de conteneur Docker

```sh
docker compose up
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

Configuration des variables d'environnement

```sh
cp .env.template .env
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
npm run test static
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

# Schema simplifié de base de données

```mermaid
---
title: Schéma simplifié les acteurs
---

classDiagram
    class ActeurService {
        - id: int
        - nom: str
        - libelle: str
        - actions: List[Action]
        + serialize(): dict
    }

    class ActeurType {
        - id: int
        - nom: str
        - libelle: str
        + serialize(): dict
        + get_digital_acteur_type_id(): int
    }

    class Source {
        - id: int
        - nom: str
        - afficher: bool
        - url: str
        - logo_file: str
        + serialize(): dict
    }

    class LabelQualite {
        - id: int
        - nom: str
        - afficher: bool
        - url: str
        - logo_file: str
        + serialize(): dict
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
        + share_url(request: HttpRequest, direction: str | None): str
        + latitude: float
        + longitude: float
        + libelle: str
        + is_digital(): bool
        + serialize(format: None | str): dict | str
        + acteur_services(): List[str]
        + proposition_services_by_direction(direction: str | None): List[PropositionService]
        + get_or_create_revision(): RevisionActeur
        + get_or_create_correctionequipe(): CorrectionEquipeActeur
        + clean_location()
        + save(*args, **kwargs)
        + set_default_field_before_save()
    }

    class DisplayedPropositionService {
        - action: Action
        - acteur_service: ActeurService
        - sous_categories: List[SousCategorieObjet]
        - acteur: Acteur
    }

    class Action {
        - id: int
        - nom: str
        - directions: List[Direction]
        - order: int
        + serialize(): dict
    }

    class Direction {
        - nom: str
        - order: int
    }

    class SousCategorieObjet {
        - id: int
        - nom: str
        - libelle: str
        + serialize(): dict
    }

    Direction --> Action
    DisplayedActeur --> DisplayedPropositionService
    ActeurType --> DisplayedActeur
    Source --> DisplayedActeur
    LabelQualite <--> DisplayedActeur
    DisplayedPropositionService <-- Action
    DisplayedPropositionService <-- ActeurService
    DisplayedPropositionService <--> SousCategorieObjet
```

```mermaid
---
title: Schéma simplifié des relations autour des acteurs
---

erDiagram
    Direction ||--|{ Action : un-n
    DisplayedActeur ||--|{ DisplayedPropositionService : un-n
    ActeurType ||--|{ DisplayedActeur : un-n
    Source ||--|{ DisplayedActeur : un-n
    Action ||--|{ DisplayedPropositionService : un-n
    ActeurService ||--|{ DisplayedPropositionService : un-n
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

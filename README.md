# Que faire de mes objets

Que faire de mes objets propose des solutions pour promouvoir les gestes de consommation responsable:

- Mise à disposition d'un annuaire d'Acteurs du ré-emploi et du re-cyclage en France (disponible aussi via une iframe)
- Mise à disposition de l'annuaire via une API
- Promotion des gestes de consommation responsable tels que le don et le partage local

## iframe et paramètres

Le site "Que faire de mes objets" est disponible à l'URL : [https://quefairedemesobjets.osc-fr1.scalingo.io/](https://quefairedemesobjets.osc-fr1.scalingo.io/)

Attention, l'URL et le nom de l'application sont temporaires.

Le site est disponible en iframe en ajoutant le paramètre `iframe` à l'URL, quelque soit sa valeur, ex : [https://quefairedemesobjets.osc-fr1.scalingo.io/?iframe](https://quefairedemesobjets.osc-fr1.scalingo.io/?iframe)

Dans le cas de l'iframe, l'entête et le pied de page ne sont pas affichés

Les autres paramètres disponibles pour afficher la page principale de l'application et permettant d'interagir avec les champs de recherche sont :

- `sous_categorie_objet`, parmi les sous-categories suivantes : `Matériel médical`, `Autre matériel de sport`, `Vélos`, `Bijou`, `montre`, `horlogerie`, `Chaussures`, `Maroquinerie`, `Vêtements`, `Jouets`, `Puériculture`, `Linge de maison`, `Vaisselle`, `Luminaires`, `Décoration`, `Mobilier`, `Jardin (mobilier`, `accessoires)`, `Outillage (bricolage/jardinage)`, `Instruments de musique`, `Livres`, `CD/DVD/jeux vidéo`, `Autres équipements électroniques`, `Photo/ciné`, `Smartphones/tablettes/consoles`, `Hifi/vidéo (hors écrans)`
- `adresse`, par exemple : 145+Avenue+Pierre+Brossolette+92120+Montrouge
- `direction`, option `jai` ou `jecherche`, par défaut la direction `jecherche` est appliquée
- `action_list`, liste des actions possibles selon la direction séparées par le caractère `|` :
  - pour la direction `jecherche` les actions possibles sont : `emprunter`, `échanger`, `louer`, `acheter+d'occasion`
  - pour la direction `jai` les actions possibles sont : `réparer`, `prêter`, `donner`, `échanger`, `mettre+en+location`, `revendre`
  - si le paramètre `action_list` n'est pas renseigné ou est vide, toutes les actions éligibles à la direction sont affichées

### Afficher l'iframe en totalité dynamiquement

Pour afficher l'iframe dans toute sa hauteur, le site, lorsqu'il est utilisé avec le paramètre iframe, embarque la librairie [iframe-resizer](https://github.com/davidjbradshaw/iframe-resizer)
Dans la page affichant l'iframe, il suffit de charge cette même librairie et d'appeler la fonction `iFrameResize` avec les bons paramètres (voir la documentation de la librairie)

Voir l'exemple de code [iframe.html](./iframe.html)

## Modèle de donnée

Chaque acteur du ré-emploi et recyclage expose des propositions de service associées à un geste et une liste de catégories d'objet

```mermaid
flowchart TD
    actor["`**Acteur du Réemploi**`"]
    service_offer["`**Proposition de Service**
    - Action -
    - Service -
    - Categories d'objet -`"]
    actor --> service_offer
```

## Environnement de développement

### Prérequis

- docker-compose
- python 3.11

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

### installation & exécution

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

### Create superuser

```sh
python manage.py createsuperuser
```

### Lancement

```sh
honcho start -f Procfile.dev
```

Honcho démarrera les containers Docker s'ils ne sont pas déjà démarrés

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

## Deploy in Scalingo

we need to install GDAL as explain in doc : [https://techilearned.com/configure-geodjango-in-scalingo/](https://techilearned.com/configure-geodjango-in-scalingo/) form [https://doc.scalingo.com/platform/app/app-with-gdal](https://doc.scalingo.com/platform/app/app-with-gdal) and mattermost discussion in beta.gouv.fr community

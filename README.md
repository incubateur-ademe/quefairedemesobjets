# Longue vie aux objets

Longue vie aux objets propose des solutions pour promouvoir les gestes de consommation responsable:

-   Mise à disposition d'une cartographie d'Acteurs du ré-emploi et de la réparation en France (disponible aussi via une iframe)
-   Promotion des gestes de consommation responsable tels que le don, le partage local et la réparation

## Afficher l'application dans une Iframe

Le site "Longue vie aux objets" est disponible à l'URL : [https://longuevieauxobjets.ademe.fr/](https://longuevieauxobjets.ademe.fr/)

Le site est disponible en iframe en ajoutant le paramètre `iframe` à l'URL, quelque soit sa valeur, ex : [https://longuevieauxobjets.ademe.fr/?iframe](https://longuevieauxobjets.ademe.fr/?iframe)

Dans le cas de l'iframe, l'entête et le pied de page ne sont pas affichés

⚠️ le tag iframe de votre page doit avoir l'attribut `allow="geolocation"` pour permettre à l'iframe d'accéder aux fonctionnalités de géolocalisation du navigateur (cf. [https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy/geolocation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy/geolocation))

### Les paramètres disponibles pour customiser l'Iframe

Les autres paramètres disponibles pour afficher la page principale de l'application et permettant d'interagir avec les champs de recherche sont :

-   `sous_categorie_objet`, parmi les sous-catégories disponibles en base de données
-   `adresse`, par exemple : 145+Avenue+Pierre+Brossolette+92120+Montrouge
-   `latitude` et `longitude` récupéré dpuis l'API BAN avec l'adresse ci-dessus
-   `direction`, option `jai` ou `jecherche`, par défaut la direction `jecherche` est appliquée
-   `action_list`, liste des actions possibles selon la direction séparées par le caractère `|` :
    -   pour la direction `jecherche` les actions possibles sont : `emprunter`, `echanger`, `louer`, `acheter`
    -   pour la direction `jai` les actions possibles sont : `reparer`, `preter`, `donner`, `echanger`, `mettreenlocation`, `revendre`
    -   si le paramètre `action_list` n'est pas renseigné ou est vide, toutes les actions éligibles à la direction sont affichées

Exemple:

```txt
https://longuevieauxobjets.ademe.fr/?direction=jecherche&action_list=emprunter%7Cechanger%7Clouer%7Cacheter+d%27occasion&sous_categorie_objet=&adresse=145+Avenue+Pierre+Brossolette+92120+Montrouge&latitude=48.815679&longitude=2.305116

```

### Afficher l'Iframe en totalité dynamiquement

Pour afficher l'iframe dans toute sa hauteur, le site, lorsqu'il est utilisé avec le paramètre iframe, embarque la librairie [iframe-resizer](https://github.com/davidjbradshaw/iframe-resizer)
Dans la page affichant l'iframe, il suffit de charge cette même librairie et d'appeler la fonction `iFrameResize` avec les bons paramètres (voir la documentation de la librairie)

Voir l'exemple de code [iframe.html](./iframe.html)

## Modèle de données

Chaque acteur du ré-emploi et recyclage expose des propositions de service associées à un geste et une liste de catégories d'objet.

### Base de données simplifiée

![Essentiel de la base de données de l'application « Longue vie aux objets »](./static/documentation_files/qdfmo-db.png)

### Objets d'administration en base de données

Certains objets de la base de données sont des objets d'administration qui n'ont pas vocation aest mis à jour régulièrement. Ci-dessous les populations de ces objets en date du 18 septembre 2023.

**Direction de l'action** (qfdmo_actiondirection):

| nom       | nom_affiche  |
| --------- | ------------ |
| jecherche | Je recherche |
| jai       | J'ai         |

**Action** (qfdmo_action):

| nom              | nom_affiche | description        | directions       |
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

**Type d'acteur** (qfdmo_acteurtype)

| nom            | nom affiché                                                |
| -------------- | ---------------------------------------------------------- |
| acteur digital | Acteur digital (site web, app. mobile)                     |
| commerce       | Franchise, enseigne commerciale                            |
| artisan        | Artisan, commerce indépendant                              |
| collectivité   | Collectivité, établissement public                         |
| ess            | Association, entreprise de l'économie sociale et solidaire |

## Environnement de développement

### Prérequis

-   docker-compose
-   python 3.11
-   node 18.17
-   gdal (librairie nécessaire à l'utilisation de GeoDjango)

Conseil: utiliser `asdf` pour la gestion des environnement virtuel `node` et `python`

#### Spécificité d'installation pour les processeur Mx de Mac

[https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e](https://gist.github.com/codingjoe/a31405952ec936beba99b059e665491e)

### Technologies

-   Python
-   Django
-   github
-   Licence MIT
-   Node
-   Parcel
-   DSFR
-   honcho
-   Scalingo
-   Sentry
-   Pytest
-   Whitnoise
-   Tailwind
-   Dependabot
-   Django-debug-toolbar

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

Population de la base (optionel, si la base de données de production est chargée sur l'environnement de développement)

```sh
python manage.py loaddata categories action_directions actions acteur_services acteur_types
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

### Import DB from production

```bash
DUMP_FILE=</path/to/dump/file.pgsql>
DATABASE_URL=postgres://qfdmo:qfdmo@localhost:6543/qfdmo

for table in $(psql "${DATABASE_URL}" -t -c "SELECT \"tablename\" FROM pg_tables WHERE schemaname='public'"); do
     psql "${DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;"
done
pg_restore -d "${DATABASE_URL}" --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}"
```

## Deploy in Scalingo

we need to install GDAL as explain in doc : [https://techilearned.com/configure-geodjango-in-scalingo/](https://techilearned.com/configure-geodjango-in-scalingo/) form [https://doc.scalingo.com/platform/app/app-with-gdal](https://doc.scalingo.com/platform/app/app-with-gdal) and mattermost discussion in beta.gouv.fr community

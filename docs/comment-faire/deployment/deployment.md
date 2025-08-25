# DevOps, déploiement, opérations

## Déploiement de la plateforme Airflow hors CD

La plateforme Data est déploié automatiquement par le processus de `Continuous Deployment`. Cependant, il est possibel d'avoir besoin de « forcer » un déploiement.

### Procédure de déploiement

#### Prérequis

- configururer sa clé ssh dans l'interface de clevercloud (cf. doc clevercloud)
- configurer un "remote repository" pour `airflow-webserver` pour ce repository et pour chaque environnemnt
- configurer un "remote repository" pour `airflow-scheduler` pour ce repository et pour chaque environnemnt
- pousser le code souhaité sur la branch master des 2 repository

#### en PREPROD

```sh
git remote add preprod-airflow-scheduler git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_3d1f7d89-d7f0-433a-ac01-c663d4729143.git
git remote add preprod-airflow-webserver git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_d3c229bf-be85-4dbd-aca2-c8df1c6166de.git
git push preprod-airflow-scheduler mabranch:master
git push preprod-airflow-webserver mabranch:master
```

#### en PROD

```sh
git remote add prod-airflow-scheduler git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_fda5d606-44d9-485f-a1b4-1f7007bc3bec.git
git remote add prod-airflow-webserver git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_efd2802a-1773-48e0-987e-7a6dffb929d1.git
git push prod-airflow-scheduler mabranch:master
git push prod-airflow-webserver mabranch:master
```

## Déploiement sur Scalingo

Nous avons besoin d'installer GDAL comme c'est expliqué dans la doc suivante : [https://techilearned.com/configure-geodjango-in-scalingo/](https://techilearned.com/configure-geodjango-in-scalingo/) cf. [https://doc.scalingo.com/platform/app/app-with-gdal](https://doc.scalingo.com/platform/app/app-with-gdal)

le code est déployé en preprod lors de la mise à jour de la branche main

et en production quand il est tagué avec en respectant le format de version semantique vX.Y.Z

### Déploiement du code de l'interface

le code de l'interface est déployé sur le repo git de scalingo à conditions que les tests soit passés avec succès via Github

## Déploiement sur CleverCloud

<!-- TODO data plateforme -->

## Deploiment sur Scaleway

<!-- TODO s3 et bientôt plus ? -->

## Accéder à un shell en production

Pour executer une commande en production, il faut au préalable se connection au shell via le CLI Scalingo.

- [Installer le CLI](https://doc.scalingo.com/platform/cli/start)

Ensuite il est possible d'ouvrir un shell (ici bash) dans le worker Scalingo.

```sh
scalingo run --app quefairedemesobjets bash
```

L'intégralité des commandes possibles n'est pas documentée ici, elle l'est dans la [documentation officielle de Django](https://docs.djangoproject.com/en/dev/ref/django-admin/#django-admin-and-manage-py)

L'ensemble des commandes documentées ci-après peut être lancée soit depuis un environnement local, soit depuis un shell en production ou pré-production.

## Rollback: Revenir à une version précédente de l'application déployée

Dans le cas d'une catastrophe en production, il est parfois nécessaire de revenir à la version précédente.
Suivez les étapes ci-dessous pour revenir à la version précédente

### Rollback des interfaces

#### Prérequis

- Prévenir l'équipe du problème de prod et du rollback à venir sur Mattermost
- Voir avec l'administrateur des données (Christian) si des modifications récentes sont à sauvegarder avant la restauration de la base de données
- Tester la procédure de rollback ci-dessous en preprod avant de l'appliquer en production

#### Rollback du code

- Vérifier le tag de version précédente sur la [page des releases github](https://github.com/incubateur-ademe/quefairedemesobjets/releases)
- Pousser le tag de la version précédente en production

```sh
git remote add prod-interface git@ssh.osc-fr1.scalingo.com:quefairedemesobjets.git
git push -f prod-interface <TAG>:master
```

#### Base de données

Restaurer la base de données avec la sauvegarde souhaitée (géréralement, la sauvegarde juste avant l'incident)

- Copier de la sauvegarde de la base de données localement à partir de l'[interface Scalingo](https://dashboard.scalingo.com/apps/osc-fr1/quefairedemesobjets/db/postgresql/backups/list)
- Déclarer les variables d'environnements ci-dessous et éxécuter la commande de restauration

```sh
DUMP_FILE=20241216001128_quefairedem_5084.tar.gz
DATABASE_URL=<Copie from scalingo env variable SCALINGO_POSTGRESQL_URL>
for table in $(psql "${DATABASE_URL}" -t -c "SELECT \"tablename\" FROM pg_tables WHERE schemaname='public'"); do
     psql "${DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;"
done
pg_restore -d "${DATABASE_URL}" --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}"
```

_TODO: refaire un script de restauration de la base de données plus simple à utiliser avec des input et tout et tout_

#### Vérifier que la restauration est effective

Accéder à la carte et jouer avec : [La carte](https://quefairedemesdechets.fr/carte)
Accéder au formulaire et joue avec : [Le formulaire](https://quefairedemesdechets.fr/formulaire)
Accéder à l'administration Django et vérifier les données qui ont été restaurée : [Admin](https://quefairedemesdechets.fr/admin)

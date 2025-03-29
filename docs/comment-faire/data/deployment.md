# Déploiement de la plateforme Airflow hors CD

La plateforme Data est déploié automatiquement par le processus de `Continuous Deployment`. Cependant, il est possibel d'avoir besoin de « forcer » un déploiement.

## Procédure de déploiement

### Prérequis

- configururer sa clé ssh dans l'interface de clevercloud (cf. doc clevercloud)
- configurer un "remote repository" pour `airflow-webserver` pour ce repository et pour chaque environnemnt
- configurer un "remote repository" pour `airflow-scheduler` pour ce repository et pour chaque environnemnt
- pousser le code souhaité sur la branch master des 2 repository

### en PREPROD

```sh
git remote add preprod-airflow-scheduler git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_3d1f7d89-d7f0-433a-ac01-c663d4729143.git
git remote add preprod-airflow-webserver git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_d3c229bf-be85-4dbd-aca2-c8df1c6166de.git
git push preprod-airflow-scheduler mabranch:master
git push preprod-airflow-webserver mabranch:master
```

### en PROD

```sh
git remote add prod-airflow-scheduler git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_fda5d606-44d9-485f-a1b4-1f7007bc3bec.git
git remote add prod-airflow-webserver git+ssh://git@push-n3-par-clevercloud-customers.services.clever-cloud.com/app_efd2802a-1773-48e0-987e-7a6dffb929d1.git
git push prod-airflow-scheduler mabranch:master
git push prod-airflow-webserver mabranch:master
```

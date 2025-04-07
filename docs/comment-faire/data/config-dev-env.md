# Configurer la plateforme DATA en environnement de développement

Copier les variable d'environnement dags/.env.template vers dags/.env

```sh
cp dags/.env.template dags/.env
```

Lancer les containers docker avec docker compose:

```sh
docker compose --profile airflow up
```

docker compose lancera :

- la base de données postgres nécessaire à la webapp de la carte
- la base de données postgres nécessaire à Airflow
- un webserver airflow
- un scheduler airflow en mode LocalExecutor

accéder à l'interface d'Airflow en local [http://localhost:8080](http://localhost:8080) ; identifiant/mot de passe : airflow / airflow

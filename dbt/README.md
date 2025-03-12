# Preuve de concept d'utilisation de dbt pour la gestion des données

## Installation

A la racine du projet

```sh
poetry install --with dev,airflow
```

Puis dans le dossier dbt

```sh
cd dbt
dbt deps
```

## Utilisation

Lancer dbt dans le dossier dbt.
L'option select permet de lancer un seul ensemble de models, cf [project.yml](./dbt_project.yml).

```sh
dbt run --select qfdmo.exhaustive_acteurs
```

Lancer les tests

```sh
dbt run --select qfdmo.exhaustive_acteurs
```

### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

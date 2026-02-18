# Preuve de concept d'utilisation de dbt pour la gestion des données

## Installation

A la racine du projet

```sh
uv install --with dev,airflow
```

Puis dans le dossier dbt

```sh
cd dbt
uv run dbt deps
```

## Utilisation

Lancer dbt dans le dossier dbt.
L'option select permet de lancer un seul ensemble de models, cf [project.yml](./dbt_project.yml).

```sh
uv run dbt run --select qfdmo.exhaustive_acteurs
```

Lancer les tests

```sh
uv run dbt run --select qfdmo.exhaustive_acteurs
```

## Sampling

- 💡 **quoi**: utiliser une sous-partie de la donnée
- 🎯 **pourquoi**: itérer plus rapidement
- 🤔 **comment**:
  - **Variable d'environement** `DBT_SAMPLING` à mettre à `true`
  - **Liberté par modèle**: d'implémenter du sampling ou pas, ex: `base_ae_etablissement.sql`
    ```sql
    {% if env_var('DBT_SAMPLING', 'false') == 'true' %}
    ORDER BY siret DESC
    LIMIT 1000000
    {% endif %}
    ```
  - **Appliquer le sampling**: en préfixant la commande dbt
    ```bash
    export DBT_SAMPLING='true' && dbt ...
    ```

### Resources:

- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

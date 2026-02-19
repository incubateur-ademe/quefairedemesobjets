# Data Platform

## Task types

- clone : get partner data to enrich ours (data.gouv, la poste, insee, annuaire-entreprise, ban…)
- source : get partner data to create new acteur (eco-organisme, cma, sinoe…)
- enrich : fix, or add datato existing actor (url, siren, siren, adresse…)
- clustering : group actor which are duplicated - shared by multiple sources
- compute acteur : to be displayed or share
- opendata : compute and share opendata
- stats : compute data quality stats
- tech : cleanup task

Some use `dbt`, other use `pandas`

```{toctree}
:maxdepth: 2

airflow.md
dbt.md
clustering-deduplication.md
```

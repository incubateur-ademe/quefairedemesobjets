# Infrastructure Scaleway

```{toctree}
:hidden:

provisioning.md
```

## Conventions

Toutes les ressouurces sur scaleway seront provisionnées dans l'organisation `Incubateur ADEME (Pathtech)` et le projet `longuevieauxobjets`

Toutes les ressources seront nommées selon le canvas `lvao-{env}-{explicite-name}` (ex : `lvao-prod-webapp-db`)

## Monitoring des bases de données

Pour monitorer les base dedonnées, Scaleway met à disposition une [interface Grafana](https://6bef58ea-39e7-4fa5-8a55-dc3999fc62df.dashboard.cockpit.fr-par.scw.cloud/d/scw-rdb-postgresql-overview/rdb-postgresql-overview?orgId=1&var-region=fr-par&refresh=5m&var-metric_datasource=f8cd3b3c-ba53-4538-b6df-c44739a568e4&var-log_datasource=cd4bcf79-05e5-49c1-8d00-df1b7390a041&var-resource_name=lvao-prod-db&var-resource_id=All&var-instance=All)

Cette interface est disponible dans l'onglet `Metrics` > `Open Grafana metrics dashboard` de l'interface de gestion de chaque base de données

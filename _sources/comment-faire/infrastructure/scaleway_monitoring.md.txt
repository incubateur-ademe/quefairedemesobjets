# Monitoring sur Scaleway

## Monitoring des bases de données

Visualiser les métriques de la base de données en accedant à l'interface Grafana du projet :
[https://6bef58ea-39e7-4fa5-8a55-dc3999fc62df.dashboard.cockpit.fr-par.scw.cloud/d/scw-rdb-postgresql-overview/rdb-postgresql-overview?orgId=1&refresh=5m](https://6bef58ea-39e7-4fa5-8a55-dc3999fc62df.dashboard.cockpit.fr-par.scw.cloud/d/scw-rdb-postgresql-overview/rdb-postgresql-overview?orgId=1&refresh=5m)

### Troubleshooting

Lors de l'installation d'une ressource, si les données de monitoring ne remontent pas dans l'interface Grafana

1. Installer le client scaleway : [https://github.com/scaleway/scaleway-cli](https://github.com/scaleway/scaleway-cli)
2. Synchroniser les data sources : [https://www.scaleway.com/en/docs/cockpit/troubleshooting/synchronize-grafana-data-sources/](https://www.scaleway.com/en/docs/cockpit/troubleshooting/synchronize-grafana-data-sources/)

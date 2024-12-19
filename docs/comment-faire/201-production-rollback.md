# Revenir à une version précédente

Dans le cas d'une catastrophe en production, il est parfois nécessaire de revenir à la version précédente.
Suivez les étapes ci-dessous pour revenir à la version précédente

## Rollback des interfaces

### Prérequis

- Prévenir l'équipe du problème de prod et du rollback à venir sur Mattermost
- Voir avec l'administrateur des données (Christian) si des modifications récentes sont à sauvegarder avant la restauration de la base de données
- Tester la procédure de rollback ci-dessous en preprod avant de l'appliquer en production

### Rollback du code

- Vérifier le tag de version précédente sur la [page des releases github](https://github.com/incubateur-ademe/quefairedemesobjets/releases)
- Pousser le tag de la version précédente en production

```sh
git remote add prod-interface git@ssh.osc-fr1.scalingo.com:quefairedemesobjets.git
git push -f prod-interface <TAG>:master
```

### Base de données

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

### Vérifier que la restauration est effective

Accéder à la carte et jouer avec : [La carte](https://lvao.ademe.fr/carte)
Accéder au formulaire et joue avec : [Le formulaire](https://lvao.ademe.fr/formulaire)
Accéder à l'administration Django et vérifier les données qui ont été restaurée : [Admin](https://lvao.ademe.fr/admin)

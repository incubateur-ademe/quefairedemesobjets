# LVAO

Ici sont référencées toutes les applications développées ou maintenues par l'équipe Longue vie aux objets

## La carte

### URLs

- Production : https://quefairedemesdechets.ademe.fr/
- Preprod : https://quefairedemesdechets.incubateur.ademe.dev/

### Accès spécifiques

Chemin d'accès aux différentes fonctionnalités

- Carte en mode formulaire : `/formulaire`
- Carte en mode carte : `/carte`
- Administration : `admin/`
- Validation de DAGs : `dags/validations`
- Configurateur d'Iframe complet (accès restreint) : `iframe/configurateur`
- Configurateur d'Iframe simplifié : `configurateur`

### Hébergement

- Preprod : https://dashboard.scalingo.com/apps/osc-fr1/quefairedemesobjets-preprod
- Production : https://dashboard.scalingo.com/apps/osc-fr1/quefairedemesobjets
- Code source : https://github.com/incubateur-ademe/quefairedemesobjets/

### Jeux de données ADEME en Open Data utilisé par la carte

- Acteur mis à disposition par les Eco-organisme : https://data.pointsapport.ademe.fr/
- Portail Open Data de l'ADEME pour publication des données LVAO : https://data.ademe.fr

## Assistant

- Production : https://quefairedemesdechets.ademe.fr
- Hébergement : https://app.netlify.com/sites/quefairedemesdechets/review
- Code source : https://github.com/incubateur-ademe/quefairedemesdechets/

### Jeux de données ADEME en Open Data utilisé par l'assistant

- https://data.ademe.fr/datasets/que-faire-de-mes-dechets-produits
- https://data.ademe.fr/datasets/que-faire-de-mes-dechets-lien

## Site institutionnel

- Production : https://longuevieauxobjets.ademe.fr/
- Preprod : https://qfdmo-preprod-cms.osc-fr1.scalingo.io/
- Code source : https://github.com/incubateur-ademe/qfdmo-sites-faciles

## Metabase

- Production : https://qfdmo-metabase.osc-fr1.scalingo.io
- Hébergement : https://dashboard.scalingo.com/apps/osc-fr1/qfdmo-metabase
- procédure de mise à jour : https://doc.incubateur.net/communaute/les-outils-de-la-communaute/autres-services/metabase/metabase

Pas de preprod

## Airflow

- Production : https://lvaoprodnlgtohal-lvao-airflow-webserver.functions.fnc.fr-par.scw.cloud
- Preprod : https://lvaopreprodbeamztby-lvao-airflow-webserver.functions.fnc.fr-par.scw.cloud
- Hébergement : https://console.scaleway.com/containers/namespaces/fr-par
  - Organisation : Incubateur ADEME (Pathtech)
  - Projet : longuevieauxobjets

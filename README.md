# Que faire de mes objets et déchets

[Que faire de mes objets et déchets](https://quefairedemesobjets.ademe.fr/) propose des solutions pour promouvoir les gestes de consommation responsable.

## Nos missions

- Mettre à disposition la cartographie des Acteurs du ré-emploi et de la réparation en France
- Promouvoir les gestes de consommation responsable tels que le don, le partage local et la réparation
- Donner les consignes de tri par objet aux citoyens

## Plusieurs services

- Un site grand public : [`https://quefairedemesobjets.ademe.fr/`](https://quefairedemesobjets.ademe.fr/)
- Carte intégrable en iframe via un script JS : [configurateur d'iframe](https://longuevieauxobjets.ademe.fr/configurateur/)
- Nos données en opendata : [Longue Vie Aux Objets - Acteurs de l'économie circulaire - Version Beta](https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire)
- Une API : contacter l'équipe pour en savoir plus

## Architecture du dépôt

L'architecture du dépôt est organisée comme suit :

```txt
/
├── .github/           # CI/CD
├── webapp/            # Application Django + Stimulus « Que faire de mes objets et déchets »
├── data-platform/     # Plateforme data (Airflow, dbt, notebooks…)
├── docs/              # Documentation technique
├── infrastructure/    # Gestion et déploiement de l'infrastructure
├── docker-compose.yml # Exécution en local
├── nginx-local-only/  # Configuration Nginx pour le dev local
├── Makefile           # Commandes globales
├── scripts/           # Scripts hors webapp
└── pyproject.toml     # Dépendances Python (uv)
```

## Documentation technique

La documentation technique est entretenue dans le dossier [`docs`](./docs/) et publiée sur GitHub Pages :

- [`https://incubateur-ademe.github.io/quefairedemesobjets/README.html`](https://incubateur-ademe.github.io/quefairedemesobjets/README.html)

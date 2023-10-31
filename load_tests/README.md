# Tests de charge pour l'application Longue vie aux objets

On utilise l'application k6 développée par Grafana

## Lancer les tests de charge

dans le répertoire `load_tests`

```sh
k6 run script.js
```

Sur le cloud grafana

```sh
k6 cloud script.js
```

## Visualiser les résultats sur Grafana

[sur l'application K6](https://app.k6.io/projects/3665897)

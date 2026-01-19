# API Que faire de mes objets

## Présentation

L'endpoint `/api/qfdmo/` expose une API REST permettant d'accéder aux données de la carte "Longue vie aux objets". Cette API permet de récupérer les informations sur les acteurs (lieux de réparation, don, etc.), les actions possibles, les catégories d'objets, et de rechercher des acteurs selon différents critères.

L'API est construite avec `django-ninja` et suit les conventions REST. Tous les endpoints retournent des données au format JSON.

## Documentation interactive

Pour les détails complets de chaque endpoint (paramètres, schémas de réponse, exemples), consultez la documentation interactive Swagger/OpenAPI disponible sur `/api/docs`.

Cette interface permet de tester tous les endpoints directement depuis le navigateur.

## Notes techniques

- Tous les endpoints retournent du JSON
- Les acteurs inactifs ne sont jamais retournés par l'API
- Les sources et sous-catégories non affichables sont filtrées
- La pagination est activée par défaut sur l'endpoint `/acteurs`
- Les coordonnées géographiques utilisent le système WGS84 (SRID 4326)
- Les distances sont calculées en utilisant PostGIS

## Tests

Les endpoints de cette API sont couverts par des tests d'intégration dans `integration_tests/carte/test_qfdmo_api.py`.

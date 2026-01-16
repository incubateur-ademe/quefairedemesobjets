# API Que faire de mes objets

## Présentation

L'endpoint `/api/qfdmo/` expose une API REST permettant d'accéder aux données de la carte "Longue vie aux objets". Cette API permet de récupérer les informations sur les acteurs (lieux de réparation, don, etc.), les actions possibles, les catégories d'objets, et de rechercher des acteurs selon différents critères.

L'API est construite avec `django-ninja` et suit les conventions REST. Tous les endpoints retournent des données au format JSON.

## Structure de l'API

L'API est organisée autour de plusieurs concepts principaux :

- **Acteurs** : Les lieux (associations, entreprises, etc.) qui proposent des services
- **Actions** : Les actions possibles sur un objet (réparer, donner, prêter, etc.)
- **Sous-catégories** : Les catégories d'objets (vêtements, électroménager, etc.)
- **Sources** : Les sources de données des acteurs
- **Services** : Les types de services proposés par les acteurs
- **Types d'acteurs** : Les catégories d'acteurs (commerce, association, etc.)

## Endpoints disponibles

- `GET /api/qfdmo/sources` - Liste des sources de données
- `GET /api/qfdmo/sous-categories` - Liste des sous-catégories d'objets
- `GET /api/qfdmo/actions` - Liste des actions possibles
- `GET /api/qfdmo/actions/groupes` - Liste des groupes d'actions
- `GET /api/qfdmo/acteurs/types` - Liste des types d'acteurs
- `GET /api/qfdmo/acteurs/services` - Liste des services proposés
- `GET /api/qfdmo/acteurs` - Recherche d'acteurs (avec pagination et filtres géographiques)
- `GET /api/qfdmo/acteur` - Détail d'un acteur spécifique
- `GET /api/qfdmo/autocomplete/configurateur` - Autocomplétion EPCI

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

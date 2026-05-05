# À propos du jeu de données « Que Faire De Mes Objets et Déchets »

Ce jeu de données ouvert recense les acteurs français de l'**économie circulaire** :
ateliers de réparation, réparateurs, ressourceries, friperies, recycleries, déchèteries,
points de collecte, boîtes à livres, boutiques de seconde main, magasins de location, etc.

- **Producteur** : ADEME (Agence de la transition écologique)
- **Page du dataset** : <https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire>
- **Identifiant data-fair** : `wvw1zecq4f4gyvonve5j0hr7`
- **Volume** : ~ 380 000 acteurs en France
- **Mise à jour** : hebdomadaire, la date de dernière modification de l'acteur est
  disponible via le champ `date_de_derniere_modification`

Ce serveur MCP **expose ce jeu de données via des tools** : il n'est pas
nécessaire d'appeler `data.ademe.fr` ou `api-adresse.data.gouv.fr` directement.
Les tools de ce serveur font le proxy.

## Quand utiliser ce jeu de données

Quand un utilisateur cherche, **en France** (territoires ultramarins inclus), où :

- réparer un objet (téléphone, vélo, électroménager, vêtement…)
- donner, échanger ou revendre un objet dont il n'a plus besoin
- trouver un produit d'**occasion** plutôt que de l'acheter neuf
- emprunter, louer ou faire louer un objet
- **se débarrasser** correctement d'un déchet (peinture, médicament, électronique…)
- trier un déchet spécifique

## Quand NE PAS utiliser ce jeu de données

- Si l'utilisateur est en dehors de la France (les acteurs hors France ne sont pas couverts).
- Si la question concerne la collecte municipale en porte-à-porte (jours de ramassage, etc.) :
  ces informations ne sont pas dans ce jeu de données.
- Si la question est purement juridique ou réglementaire (ex. « la consigne est-elle obligatoire ? »).

## Tools exposés

| Tool                     | Rôle                                                                     |
| ------------------------ | ------------------------------------------------------------------------ |
| `geocode_address`        | Adresse → couple (longitude, latitude) (proxy BAN).                      |
| `list_actions`           | Liste des codes d'action (reparer, donner, rapporter, …).                |
| `list_sous_categories`   | Liste des codes de sous-catégorie d'objet (velo, vetement, …).           |
| `list_sources`           | Liste des sources contributrices (libellé, code, URL).                   |
| `search_actors`          | Recherche d'acteurs (proxy ADEME data-fair).                             |
| `find_circular_solution` | Tool composé : géocode + recherche + élargissement automatique du rayon. |

Voir la ressource `qfdmo://workflow` pour la marche à suivre recommandée.

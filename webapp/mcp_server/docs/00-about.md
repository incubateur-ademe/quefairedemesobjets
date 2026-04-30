# À propos du jeu de données « Que Faire De Mes Objets et Déchets »

Ce jeu de données ouvert recense les acteurs français de l'**économie circulaire** :
ateliers de réparation, ressourceries, recycleries, déchèteries, points de collecte,
boutiques de seconde main, magasins de location, etc.

- **Producteur** : ADEME (Agence de la transition écologique)
- **Page du dataset** : <https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire>
- **Identifiant data-fair** : `wvw1zecq4f4gyvonve5j0hr7`
- **Volume** : ~ 380 000 acteurs en France
- **Mise à jour** : régulière, voir le champ `date_de_derniere_modification` de chaque ligne

## Quand utiliser ce jeu de données

Quand un utilisateur cherche, **en France**, où :

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

## Workflow recommandé pour répondre

Voir la ressource `qfdmo://workflow`. En résumé :

1. Demander la **localisation** (avec consentement explicite).
2. Identifier la **sous-catégorie** de l'objet (ressource `qfdmo://sous-categories`).
3. Identifier l'**action** souhaitée (ressource `qfdmo://actions`).
4. **Géocoder** l'adresse via l'API BAN (ressource `qfdmo://geocoding`).
5. Interroger l'API ADEME `/lines` (ressource `qfdmo://search-api`).
6. Restituer les résultats avec nom, adresse, distance, horaires, lien.

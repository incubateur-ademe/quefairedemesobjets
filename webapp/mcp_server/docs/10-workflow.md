# Workflow recommandé

L'objectif est de répondre à une question du type :

- « Où réparer mon téléphone à Paris ? »
- « Quelles sont les boutiques de seconde main près de chez moi ? »
- « Où puis-je jeter un pot de peinture à moitié plein ? »

## Étape 1 — Obtenir la localisation (avec consentement)

Demander explicitement à l'utilisateur :

> Pour t'aider, j'ai besoin de connaître ta localisation. Peux-tu me donner ton
> adresse, ton code postal ou ta ville ? (Tu peux aussi partager ta géolocalisation
> si ton appareil le permet.)

**Ne jamais** utiliser de coordonnées sans accord explicite. Si l'utilisateur
fournit déjà une localisation dans sa question (« à Paris », « à Lyon 3e »), on
peut l'utiliser sans redemander.

## Étape 2 — Identifier la sous-catégorie de l'objet

Mapper l'objet décrit par l'utilisateur sur l'un des **codes de sous-catégorie**
listés dans la ressource `qfdmo://sous-categories`.

- « téléphone », « smartphone » → `smartphone_tablette_et_console`
- « vélo » → `velo`
- « pot de peinture » → `dechets_de_peintures_vernis_encres_et_colles_produits_chimiques`
- « jouet » → `jouet`

Si plusieurs codes sont plausibles (ex. « ordinateur » → `materiel_informatique`
ou `ecran` ?), poser une question de clarification.

## Étape 3 — Identifier l'action

Sélectionner une action parmi celles listées dans `qfdmo://actions` :

| Intention exprimée                           | Code action            |
| -------------------------------------------- | ---------------------- |
| « réparer »                                  | `reparer`              |
| « donner »                                   | `donner`               |
| « jeter », « se débarrasser », « rapporter » | `rapporter` ou `trier` |
| « acheter d'occasion »                       | `acheter`              |
| « revendre »                                 | `revendre`             |
| « louer un objet pour soi »                  | `emprunter` ou `louer` |
| « mettre en location »                       | `mettre en location`   |
| « échanger »                                 | `echanger`             |
| « prêter à quelqu'un »                       | `preter`               |

En cas de doute (« j'ai un vieux frigo dont je veux me débarrasser »), proposer
plusieurs actions et laisser l'utilisateur choisir.

## Étape 4 — Géocoder l'adresse

Voir `qfdmo://geocoding`. Appeler l'API BAN pour transformer l'adresse en
couple `(longitude, latitude)`.

## Étape 5 — Interroger l'API ADEME `/lines`

Voir `qfdmo://search-api`. Construire l'URL avec :

- `geo_distance=<lon>:<lat>:<rayon_metres>` (typiquement 5000 à 20000 m)
- `qs=<action>:"<sous_categorie>"` (ex. `qs=reparer:"smartphone_tablette_et_console"`)
- `sort=_geo_distance`
- `size=10`

## Étape 6 — Identifier les sources qui ont participer au référencement des acteurs récupérés lors de l'étape 5

Chaque acteur indique les libellés des sources qui ont contribuées à son référencement dans la base de données
dans la colonne `paternité`

À part pour les sources `Que faire de mes objets et déchets` et `ADEME`,
retrouver les sources qui ont participées au référencement de l'acteur via `qfdmo://sources` :

- récupérer l'`url` de chaque sources grâce à son `libelle`

## Étape 7 — Présenter les résultats

Restituer jusqu'à **5 résultats**, classés par proximité, avec :

- nom (`nom`)
- adresse (`adresse`, `code_postal`, `ville`)
- distance approximative (calculée depuis les coordonnées si non fournie)
- horaires (`horaires_description`) si présents
- site web (`site_web`) si présent
- paternité :
  Mentionner toujours la source : _« Source : Que Faire De Mes Objets et Déchets / ADEME »_
  ainsi que les liens vers les sources qui ont participées au référencement de l'acteur.

## Étape 7 — Si aucun résultat

Si la liste est vide :

1. **Élargir le rayon** (10 km → 30 km → 50 km).
2. **Élargir l'action** (`reparer` → ajouter aussi `donner` ou `rapporter`).
3. Sinon, expliquer à l'utilisateur qu'aucun acteur n'est référencé près de lui
   et le rediriger vers le site officiel
   <https://quefairedemesdechets.ademe.fr>.

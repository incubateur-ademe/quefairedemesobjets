# Workflow recommandé

L'objectif est de répondre à une question du type :

- « Où réparer mon téléphone à Paris ? »
- « Quelles sont les boutiques de seconde main près de chez moi ? »
- « Où puis-je jeter un pot de peinture à moitié plein ? »

Toutes les étapes ci-dessous se font **uniquement via les tools MCP**.
N'invoque jamais directement les URLs des APIs upstream.

## Étape 1 — Obtenir la localisation (avec consentement)

Demander explicitement à l'utilisateur :

> Pour t'aider, j'ai besoin de connaître ta localisation. Peux-tu me donner ton
> adresse, ton code postal ou ta ville ? (Tu peux aussi partager ta géolocalisation
> si ton appareil le permet.)

**Ne jamais** utiliser de coordonnées sans accord explicite. Si l'utilisateur
fournit déjà une localisation dans sa question (« à Paris », « à Lyon 3e »), on
peut l'utiliser sans redemander.

## Étape 2 — Identifier la sous-catégorie de l'objet

Appeler `list_sous_categories(query=<mot-clé>)` pour obtenir le code à utiliser.

Quelques exemples :

- « téléphone », « smartphone » → `smartphone_tablette_et_console`
- « vélo » → `velo`
- « pot de peinture » → `dechets_de_peintures_vernis_encres_et_colles_produits_chimiques`
- « jouet » → `jouet`

Si plusieurs codes sont plausibles (ex. « ordinateur » → `materiel_informatique`
ou `ecran` ?), poser une question de clarification.

## Étape 3 — Identifier l'action

Appeler `list_actions(query=<mot-clé>)` pour choisir le code d'action.

| Intention exprimée                           | Code action            |
| -------------------------------------------- | ---------------------- |
| « réparer »                                  | `reparer`              |
| « donner »                                   | `donner`               |
| « jeter », « se débarrasser », « rapporter » | `rapporter` ou `trier` |
| « acheter d'occasion »                       | `acheter`              |
| « revendre »                                 | `revendre`             |
| « louer un objet pour soi »                  | `emprunter` ou `louer` |
| « mettre en location »                       | `mettreenlocation`     |
| « échanger »                                 | `echanger`             |
| « prêter à quelqu'un »                       | `preter`               |

En cas de doute (« j'ai un vieux frigo dont je veux me débarrasser »), proposer
plusieurs actions et laisser l'utilisateur choisir.

## Étape 4 — Rechercher les acteurs

Privilégier le tool composé `find_circular_solution` :

```text
find_circular_solution(
  address="Paris",
  action="reparer",
  sous_categorie="smartphone_tablette_et_console",
  radius_meters=5000  # optionnel, défaut 5000
)
```

Ce tool :

1. géocode l'adresse via la BAN ;
2. interroge l'API ADEME data-fair ;
3. **élargit automatiquement le rayon** (×2 jusqu'à 50 km) si zéro résultat.

Si tu as déjà des coordonnées, tu peux aussi enchaîner manuellement
`geocode_address` puis `search_actors`.

## Étape 5 — Enrichir la paternité

Chaque acteur expose un champ `paternite` (libellés de sources contributrices
séparés par `|`). Pour chaque libellé **autre que** « Que faire de mes objets et
déchets » et « ADEME », appeler `list_sources(libelle_contains=<libelle>)` pour
récupérer son URL et l'inclure dans la restitution.

## Étape 6 — Présenter les résultats

Restituer jusqu'à **5 résultats**, classés par proximité, avec :

- nom (`nom`)
- adresse (`adresse`, `code_postal`, `ville`)
- distance approximative (`distance_m`, en mètres)
- horaires (`horaires_description`) si présents
- site web (`site_web`) si présent
- paternité : liste des libellés et liens, plus la mention finale
  _« Source : Que Faire De Mes Objets et Déchets / ADEME »_

## Étape 7 — Si aucun résultat

`find_circular_solution` ayant déjà élargi jusqu'à 50 km, expliquer à
l'utilisateur qu'aucun acteur n'est référencé près de chez lui et le rediriger
vers <https://quefairedemesdechets.ademe.fr>.

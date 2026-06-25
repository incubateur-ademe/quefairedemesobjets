# Exemples concrets

Quelques scénarios complets exprimés en appels de tools. Tous les appels
HTTP vers la BAN ou ADEME sont effectués par le serveur MCP — le client n'a
qu'à invoquer les tools.

## Exemple 1 — Réparer un téléphone à Paris

**Question** : « Où réparer mon téléphone à Paris ? »

```text
find_circular_solution(
  address="Paris",
  action="reparer",
  sous_categorie="smartphone_tablette_et_console"
)
```

Le tool géocode `Paris` (BAN), interroge l'API ADEME, et renvoie jusqu'à 10
acteurs triés par proximité.

## Exemple 2 — Donner des vêtements à Lyon

```text
find_circular_solution(
  address="Lyon",
  action="donner",
  sous_categorie="vetement"
)
```

## Exemple 3 — Jeter un pot de peinture à moitié plein à Toulouse

C'est un déchet dangereux : code
`dechets_de_peintures_vernis_encres_et_colles_produits_chimiques`, action
`rapporter`.

```text
find_circular_solution(
  address="Toulouse",
  action="rapporter",
  sous_categorie="dechets_de_peintures_vernis_encres_et_colles_produits_chimiques",
  radius_meters=10000
)
```

## Exemple 4 — Acheter un vélo d'occasion à Bordeaux

```text
find_circular_solution(
  address="Bordeaux",
  action="acheter",
  sous_categorie="velo"
)
```

## Exemple 5 — Louer une perceuse à Rennes

```text
find_circular_solution(
  address="Rennes",
  action="louer",
  sous_categorie="outil_de_bricolage_et_jardinage"
)
```

## Exemple 6 — Rapporter des médicaments à Marseille

Pour les médicaments, le canal officiel est la **pharmacie** (filière
Cyclamed). On peut tout de même chercher les points enregistrés :

```text
find_circular_solution(
  address="Marseille",
  action="rapporter",
  sous_categorie="medicaments",
  radius_meters=3000
)
```

## Exemple 7 — Recherche en deux étapes (coordonnées déjà connues)

Si les coordonnées sont déjà connues (ex. obtenues par un autre tool ou par
géolocalisation explicite de l'utilisateur), on peut sauter le géocodage :

```text
search_actors(
  longitude=2.3522,
  latitude=48.8566,
  action="reparer",
  sous_categorie="velo",
  radius_meters=5000
)
```

## Exemple 8 — Découvrir les codes via les tools de listing

Avant la recherche, on peut s'aider de :

```text
list_actions(query="rep")              # → reparer
list_sous_categories(query="peinture") # → dechets_de_peintures_…
```

## Astuces

- `find_circular_solution` élargit déjà le rayon automatiquement (×2 jusqu'à
  50 km). Ne pas réimplémenter cette logique côté client.
- Toujours conclure la réponse à l'utilisateur par : _« Source : Que Faire De
  Mes Objets et Déchets / ADEME »_, accompagnée des URLs des sources
  contributrices obtenues via `list_sources`.

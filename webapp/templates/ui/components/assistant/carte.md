# Carte de l'assistant

Carte MapLibre affichant au plus 20 lieux proposant un geste, mise à jour
pendant l'exploration.

## Comment l'utiliser

```django
{% include "ui/components/assistant/carte.html" with
   geste="reparer"
   objet="telephone-mobile"
   longitude=2.3488
   latitude=48.8534
   couleur_geste="#009081"
   lieux=lieux %}
```

| Paramètre       | Requis | Rôle                                                        |
| --------------- | ------ | ----------------------------------------------------------- |
| `geste`         | ✅     | code d'un `GroupeAction` — voir ci-dessous                  |
| `longitude`     | ✅     | centre initial                                              |
| `latitude`      | ✅     | centre initial                                              |
| `couleur_geste` | ✅     | couleur des pinpoints, issue de `GroupeAction.couleur`      |
| `objet`         | ⚪️     | slug d'une fiche, restreint les lieux à ses sous-catégories |
| `lieux`         | ⚪️     | liste rendue côté serveur pour la version accessible        |

> ⚠️ `geste` attend un code de **`GroupeAction`** (`reparer`,
> `donner_echanger_rapporter`, `emprunter_preter_louer`, `vendre_acheter`,
> `trier`) et non d'`Action`. Un `geste="deposer"` ne correspond à rien : le
> code attendu est `trier`.

## Découpage du code

Trois fichiers, chacun avec une responsabilité unique. Le découpage suit la
logique d'un composant React : une couche de données pure, une couche de rendu,
un contrôleur qui orchestre.

```
js/assistant/lieux_visibles.ts   logique pure, testée sans navigateur
js/assistant/pinpoint.ts         fabrication des éléments DOM
controllers/assistant/carte_controller.ts   cycle de vie et requêtes
```

| Fichier             | Responsabilité                                         | Ne fait pas                     |
| ------------------- | ------------------------------------------------------ | ------------------------------- |
| `lieux_visibles.ts` | fusion, filtrage par zone, plafond de 20               | aucun accès au DOM ni au réseau |
| `pinpoint.ts`       | élément DOM d'un marqueur, couleur, libellé accessible | ne connaît pas la carte         |
| `carte_controller`  | MapLibre, `fetch`, annonces, nettoyage                 | ne calcule aucune règle métier  |

La logique métier vit dans `lieux_visibles.ts`, sans dépendance au navigateur :
elle se teste en Jest, sans monter de carte.

## Les règles métier implémentées

Toutes viennent de la spec
[#3356](https://app.notion.com/p/3a06523d57d780589476d537f8776008).

### Rafraîchissement après une seconde d'immobilité

```typescript
static debounces = [{ name: "rafraichir", wait: DELAI_STABILISATION_MS }]
```

Rien ne se passe pendant que l'usager déplace ou zoome. `useDebounce` de
`stimulus-use` applique les défauts `leading: false, trailing: true`, soit
exactement « attendre que ça s'arrête ».

### Un point visible ne disparaît pas

C'est la règle la plus subtile, et la raison pour laquelle l'endpoint renvoie
du GeoJSON plutôt que du HTML : le client doit posséder l'état des marqueurs
pour comparer l'ancien et le nouveau.

```typescript
const conserves = affiches.filter((lieu) => estDansLaZone(lieu, zone))
const fusion = new Map(conserves.map((lieu) => [lieu.uuid, lieu]))
for (const lieu of nouveaux) {
  if (fusion.size >= plafond) break
  fusion.set(lieu.uuid, lieu)
}
```

Les lieux conservés sont insérés **en premier** : ce sont eux qui remplissent
le plafond de 20. Un lieu sous les yeux de l'usager ne saute donc jamais, ce
qui répond à un retour de test explicite.

### Dézoom : masqués, pas perdus

Sous le zoom d'un département, les marqueurs sont retirés de la carte mais
`this.lieux` est conservé. Un rezoom les réaffiche **sans requête**.

### Requêtes annulables

```typescript
this.requeteEnCours?.abort()
this.requeteEnCours = new AbortController()
```

Sans cela, une réponse lente arrivant après une réponse récente repeindrait une
zone déjà quittée. Un usager qui balaie la carte enchaîne les rafraîchissements :
le scintillement serait visible.

## Points d'attention

### `disconnect()` est obligatoire

```typescript
disconnect() {
  this.requeteEnCours?.abort()
  this.marqueurs.forEach((marqueur) => marqueur.remove())
  this.carte?.remove()
}
```

Sans `carte.remove()`, le contexte WebGL fuit à chaque navigation de Turbo
Frame. Le problème a déjà été rencontré sur la carte V1.

### Une méthode débouncée ne peut pas être `await`ée

`useDebounce` remplace la méthode par une enveloppe qui **ne retourne rien**.
`await this.rafraichir()` résout immédiatement sur `undefined`, et
`.catch()` lève. C'est pourquoi `rafraichir()` gère ses propres erreurs : un
rejet non capturé deviendrait une _unhandled promise rejection_ silencieuse.

### MapLibre est chargé dynamiquement

```typescript
const { Map, Marker, NavigationControl } = await import("maplibre-gl")
```

MapLibre pèse 21 Mo sur disque. L'import statique le placerait dans le bundle
de toutes les pages, y compris l'accueil et la fiche objet qui n'affichent
aucune carte.

### La couleur suit le geste, pas le lieu

Un même acteur s'affiche en bleu si l'usager a choisi « donner » et en brun
s'il a choisi « revendre ». La couleur vient donc du template
(`--qfa-geste-couleur`, alimenté par `GroupeAction.couleur` en base), jamais
d'une propriété du lieu. Seul le Bonus Réparation prend le pas.

## Accessibilité

Une carte MapLibre n'est ni navigable au clavier ni lisible par un lecteur
d'écran. Le composant rend donc **toujours** une liste des lieux côté serveur,
qui reste le chemin accessible tant que la bascule liste/carte n'existe pas.

Les messages d'état (« aucun lieu », « zoomez sur la carte ») sont annoncés via
un conteneur `role="status" aria-live="polite"` présent dès le chargement :
injecté après coup, il ne serait pas annoncé par certains lecteurs d'écran.

`role="status"` plutôt que `role="alert"` : l'information est utile, pas
urgente, et `alert` interromprait la lecture en cours.

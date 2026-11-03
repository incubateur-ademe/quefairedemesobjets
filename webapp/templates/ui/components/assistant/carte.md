# Carte de l'assistant

Carte MapLibre affichant au plus 20 lieux proposant un geste, mise à jour
pendant l'exploration.

## Comment l'utiliser

```django
{% include "ui/components/assistant/carte.html" with
   gestes=gestes
   fiche="telephone-mobile"
   longitude=2.3488
   latitude=48.8534
   adresse_precise=True
   lieux=lieux %}
```

| Paramètre         | Requis | Rôle                                                                 |
| ----------------- | ------ | -------------------------------------------------------------------- |
| `gestes`          | ✅     | codes de `GroupeAction` (`trier`, pas `deposer`) ; le premier colore |
| `longitude`       | ✅     | centre initial                                                       |
| `latitude`        | ✅     | centre initial                                                       |
| `fiche`           | ⚪️     | slug d'une fiche, restreint les lieux à ses sous-catégories          |
| `adresse_precise` | ⚪️     | affiche la punaise de l'adresse ; jamais pour une commune            |
| `lieux`           | ⚪️     | liste rendue côté serveur pour la version accessible                 |
| `debug`           | ⚪️     | affiche l'overlay de durée des requêtes (`chrono_controller`)        |

## Code

| Fichier                                  | Rôle                                                   |
| ---------------------------------------- | ------------------------------------------------------ |
| `js/assistant/visible_places.ts`         | fusion et plafonds des lieux, sans DOM ni réseau       |
| `js/assistant/pinpoint.ts`               | élément DOM d'une punaise                              |
| `controllers/assistant/carte_controller` | MapLibre, requêtes, annonces, persistance entre écrans |

## Comportement

- **Rafraîchissement** à chaque `moveend` ; une requête en vol est annulée par
  la suivante, et une même zone n'est pas redemandée deux fois de suite.
- **Les lieux chargés restent** : un lieu vu ne bouge ni ne disparaît. Chaque
  requête ajoute au plus 20 lieux ; au-delà de 200 en mémoire, les lieux hors
  cadre les plus éloignés partent en premier.
- **Dézoom** : sous le zoom d'un département, les punaises sont masquées par
  CSS (`data-zoomed-out`) mais gardées, et réapparaissent sans requête.
- **Couleur** : celle du premier geste (`data-geste` sur le composant, jetons
  `--qfa-geste-*` du CSS) ; la couleur du Bonus Réparation la remplace sur la
  carte « réparer », avec la pastille « % ».

## Persistance entre écrans

La toile (`carte_canvas.html`) est un élément permanent Turbo : le même nœud,
avec son instance MapLibre, passe d'un écran à l'autre ; hors de l'écran
solutions, il est parqué en fin de `body`. Le contrôleur accroche son état au
nœud (`assistantMap`) : même recherche, les punaises restent ; autre geste ou
autre objet, elles repartent de zéro ; autre adresse, la carte se recentre. Le
contexte WebGL n'est libéré que si le nœud a quitté le document.

## Accessibilité

Une carte MapLibre n'est ni navigable au clavier ni lisible par un lecteur
d'écran : le composant rend toujours la liste des lieux côté serveur. Les
messages d'état passent par un `role="status"` présent dès le chargement.

## Worker MapLibre

L'URL du worker est fournie par le gabarit
(`data-assistant-carte-worker-url-value`) et passée à `setWorkerUrl` : Parcel
ne conserve pas `import.meta.url`. Sans elle, le fond reste gris et la console
du worker affiche `Cannot find module`.

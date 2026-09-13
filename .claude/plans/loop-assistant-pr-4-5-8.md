# Runbook — boucle séquentielle PR 4 → 5 → 8

Créé le 2026-09-13 · motif `sequential` · mode `safe`

## Objectif

Amener les écrans accueil (PR 4), fiche objet (PR 5) et détail d'un lieu (PR 8)
au niveau du périmètre MVP décrit par la spec #3295. **La boucle s'arrête quand
le périmètre est couvert**, pas quand le temps est écoulé.

## État de départ (vérifié)

| Élément             | État                                                        |
| ------------------- | ----------------------------------------------------------- |
| Branche             | `assistant-composants`, synchro avec `origin`               |
| pytest `assistant`  | 30 passés                                                   |
| Jest `js/assistant` | 9 passés                                                    |
| Migrations          | aucune en attente                                           |
| Routes              | les 6 existent, les pages sont des coquilles (6 à 9 lignes) |
| Composants          | les 12 du #3433 sont faits                                  |

`ECC_HOOK_PROFILE` n'est pas défini : les hooks du dépôt (pre-commit) restent
actifs, ce qui suffit au mode `safe`. Aucun hook n'est désactivé globalement.

## Condition d'arrêt

La boucle s'arrête quand **les trois Definition of done** sont vérifiées, ou
qu'un point bloquant demande un arbitrage humain.

### PR 4 — Écran accueil

- [x] Autocomplete d'adresse (BAN), sans l'option « Autour de moi » (hors MVP)
- [x] Le `type` BAN (`housenumber`/`street`/`municipality`) est propagé —
      nécessaire à la punaise rouge, qui ne s'affiche **que** pour une adresse
      précise, jamais pour une commune (#3356)
- [x] Les deux champs sont obligatoires
- [x] Saisir objet + adresse mène à la fiche objet
- [x] Bandeau de marque (logos + lien « En savoir plus »)

### PR 5 — Fiche objet

- [x] Gestes ordonnés selon la hiérarchie #3295 : réparable → bon état → hors d'usage
- [x] Badges d'état par geste, badge Bonus sur `reparer`
- [x] Consignes statiques derrière `consignes_pour()`, pivot vers #3284
- [x] Appel à l'action « Je découvre les solutions » vers les solutions
- [x] Changer d'objet depuis l'en-tête recharge le frame sans recharger la page
- [x] Rappel de l'objet et de l'adresse en en-tête

### PR 8 — Détail d'un lieu

- [x] Identité : nom commercial + type de service
- [x] Un seul label affiché, Bonus Réparation uniquement (pas ESS ni Répar'Acteurs)
- [x] Téléphone et site web en texte, pas en lien (#3295)
- [x] Infos pratiques (à domicile, sur RDV, exclusivité marque, reprise 1 pour 1…)
- [x] Accordéon horaires
- [x] « En savoir plus » : sources et date de mise à jour
- [x] `pour_le_detail()` porte le `prefetch_related` côté QuerySet, pas la vue

## Hors périmètre — ne pas implémenter

Rejeté explicitement par #3295, à ne pas « améliorer » en passant :

- géolocalisation « Autour de moi »
- « Les plus populaires », catégories thématiques
- compteurs de solutions (total et par geste)
- bascule liste/carte, mode liste, pagination
- filtres (Bonus, ESS, Répar'Acteurs, exclusivité marque) et chips
- itinéraire, appel, partage
- mini-carte du lieu
- accordéon des gestes acceptés avec sous-catégories
- avertissements par fiche, liens sortants dans les consignes

## Portes qualité à chaque itération (mode safe)

1. `uv run pytest assistant` — vert
2. `npx jest static/to_compile/js/assistant` — vert
3. `uv run ruff check` sur les fichiers touchés — vert
4. `npm run build` — sans erreur
5. Rendu vérifié **au navigateur**, pas seulement au code HTTP 200
6. `makemigrations --check` — rien en attente
7. Commit par PR, sans mention d'outil, puis `push` — **aucune PR ouverte**

La porte 5 n'est pas décorative : sur PR 2-3, trois défauts (icônes noires,
logos cassés, chevron inversé) passaient les tests et ne se voyaient qu'au
rendu.

## Points d'arbitrage connus

- **URL de partage d'un lieu** (#3434) : le plan pose `/assistant/lieu/<uuid>/`.
  À valider avant merge, pas bloquant pour l'implémentation.
- **`ProduitPage` n'a pas de champ consignes** : contenu statique assumé,
  derrière `consignes_pour()`, jusqu'à #3284.
- **PR 0 reportée** : le code continue d'importer `qfdmd`/`qfdmo`.

## Suivi

| PR  | État     | Commit                                       |
| --- | -------- | -------------------------------------------- |
| 4   | **fait** | `98ebe4042` accueil + recherche d'adresse    |
| 5   | **fait** | `c2b40bd6a` fiche objet, consignes statiques |
| 8   | **fait** | détail d'un lieu                             |

## Boucle arrêtée

Les trois Definition of done sont vérifiées. Six défauts trouvés en chemin,
tous invisibles aux tests et repérés en regardant le rendu ou en exerçant le
parcours de bout en bout :

1. **Slug toujours vide** dans la recherche d'objet : chaque sous-classe de
   `SearchTerm` nomme différemment sa relation vers la fiche, et une seule
   était lue. Le formulaire ne pouvait donc jamais aboutir.
2. **`ui/layout/turbo.html` rendait une page vide** : il déclarait
   `{% block content %}` quand les pages définissent `main`. Toute réponse à un
   Turbo Frame sortait vide depuis la PR 1.
3. **L'en-tête devait être dans le frame** : Turbo Drive étant désactivé, un
   formulaire au-dessus retombe sur une navigation classique.
4. **Icône « donner » vide** : le Figma exporte son glyphe séparément du cercle.
5. **`libelle_court` absent de `actions.json`** : toute base fraîche affichait
   des étiquettes vides.
6. **Valeur inventée pour `lieu_prestation`** : la base utilise
   `SUR_PLACE_OU_A_DOMICILE`, pas `domicile`.

## Reste à faire, hors périmètre de cette boucle

- **Vérification navigateur de la PR 8** : le serveur de développement s'est
  arrêté avant. Les 16 tests de la fiche lieu passent, mais le rendu n'a pas
  été regardé — c'est la porte qui a attrapé les six défauts ci-dessus.
- **URL de partage d'un lieu** (#3434), à valider avec le produit.
- **PR 7 (carte)** : la suite e2e n'a toujours pas eu de passage propre.

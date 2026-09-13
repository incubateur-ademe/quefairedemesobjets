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

- [ ] Autocomplete d'adresse (BAN), sans l'option « Autour de moi » (hors MVP)
- [ ] Le `type` BAN (`housenumber`/`street`/`municipality`) est propagé —
      nécessaire à la punaise rouge, qui ne s'affiche **que** pour une adresse
      précise, jamais pour une commune (#3356)
- [ ] Les deux champs sont obligatoires
- [ ] Saisir objet + adresse mène à la fiche objet
- [ ] Bandeau de marque (logos + lien « En savoir plus »)

### PR 5 — Fiche objet

- [ ] Gestes ordonnés selon la hiérarchie #3295 : réparable → bon état → hors d'usage
- [ ] Badges d'état par geste, badge Bonus sur `reparer`
- [ ] Consignes statiques derrière `consignes_pour()`, pivot vers #3284
- [ ] Appel à l'action « Je découvre les solutions » vers les solutions
- [ ] Changer d'objet depuis l'en-tête recharge le frame sans recharger la page
- [ ] Rappel de l'objet et de l'adresse en en-tête

### PR 8 — Détail d'un lieu

- [ ] Identité : nom commercial + type de service
- [ ] Un seul label affiché, Bonus Réparation uniquement (pas ESS ni Répar'Acteurs)
- [ ] Téléphone et site web en texte, pas en lien (#3295)
- [ ] Infos pratiques (à domicile, sur RDV, exclusivité marque, reprise 1 pour 1…)
- [ ] Accordéon horaires
- [ ] « En savoir plus » : sources et date de mise à jour
- [ ] `pour_le_detail()` porte le `prefetch_related` côté QuerySet, pas la vue

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

| PR  | État    | Commit |
| --- | ------- | ------ |
| 4   | à faire |        |
| 5   | à faire |        |
| 8   | à faire |        |

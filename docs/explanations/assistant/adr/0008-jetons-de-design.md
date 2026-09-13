# Décision 0008 : relever les jetons dans le Figma plutôt que les approximer

Date : 2026-09-13

## Statut

Accepté — mis en œuvre dans `static/to_compile/styles/assistant.css`

## Contexte

Les premières versions de la carte et des pinpoints ont été écrites sans accès
au Figma. Trois éléments étaient donc des approximations assumées :

| Élément             | Approximation                      | Réalité du Figma              |
| ------------------- | ---------------------------------- | ----------------------------- |
| Forme du pinpoint   | `clip-path` dessiné à la main      | goutte 35×47, pointe à y=47   |
| Remplissage         | aplat de la couleur du geste       | corps blanc + cerne + icône   |
| Rayon des angles    | `--qfa-rayon: 8px`                 | `--radius-sm: 4`              |
| Couleurs des gestes | dérivées de `GroupeAction.couleur` | jetons d'illustration du DSFR |

Le MCP Figma ayant été connecté, ces valeurs ont pu être relevées directement
sur le nœud `368:1591` (« Carte/Punaises de carte »).

## Décision

Les couleurs de geste deviennent des jetons nommés par le geste, pas par la
teinte — un nom de couleur devient faux dès que le design change :

```css
--qfa-geste-reparation: #009081; /* green-menthe-main-548 */
--qfa-geste-don: #417dc4; /* blue-cumulus-main-526 */
--qfa-geste-vente: #bb8568; /* brown-caramel-sun-425-hover */
--qfa-geste-loc: #ce614a; /* pink-tuile-main-556 */
--qfa-geste-tri: #a558a0; /* purple-glycine-main-494 */
```

Les SVG exportés du Figma servent de **masques CSS** plutôt que d'images : la
forme reste exactement celle de la maquette, et la couleur continue de venir
de `--qfa-pinpoint-couleur`, donc du geste choisi par l'usager (#3295).

> ⚠️ Parcel refuse une `url()` relative dans une custom property : elle se
> résout là où le `var()` est utilisé, pas là où il est défini. Les masques
> sont donc écrits directement dans `mask-image`, jamais via une variable.

## Deux écarts constatés, non tranchés

**1. `vendre_acheter` diverge.** Quatre des cinq couleurs correspondent déjà à
`GroupeAction.couleur` en base, ce qui confirme que le Figma est la source de
ces valeurs. La cinquième non :

| Code                        | En base   | Figma     |
| --------------------------- | --------- | --------- |
| `reparer`                   | `#009081` | `#009081` |
| `donner_echanger_rapporter` | `#417dc4` | `#417DC4` |
| `emprunter_preter_louer`    | `#ce614a` | `#CE614A` |
| `vendre_acheter`            | `#D1B781` | `#BB8568` |
| `trier`                     | `#A558A0` | `#A558A0` |

La carte utilise la valeur du Figma. **À trancher avec le design** : soit la
base est en retard, soit le Figma l'est.

**2. La spec et le Figma se contredisent sur un libellé.** #3295 décrit
« Prêter/Louer = orange » ; le Figma utilise `pink-tuile` (#CE614A), un
terracotta. La maquette fait foi, la spec décrit une intention.

## La typographie reste ouverte

Le composant « Barre de recherche » (nœud `24417:448`) est en **Public Sans**,
alors que la page des pinpoints est en **Marianne**. Marianne est déjà
embarquée via le DSFR ; Public Sans ne l'est pas.

Comme [ADR 0001](0001-pas-de-dsfr.md) écarte le DSFR de l'assistant, ajouter
une police revient à embarquer un webfont de plus. La décision n'est pas prise
ici : l'assistant n'impose aucune `font-family` pour l'instant.

## Conséquences

- Les pinpoints sont conformes à la maquette, vérifié au rendu.
- Un changement de couleur de geste se fait en un endroit.
- **Les assets sont copiés, pas liés** : une évolution du Figma ne se propage
  pas toute seule. C'est le prix d'un rendu qui ne dépend pas du réseau.
- Les jetons de dimension (`--radius-sm: 4`, `--spacing-3v: 12`) ne sont pas
  encore repris : `--qfa-rayon` vaut toujours 8px, à aligner quand les
  composants élémentaires seront construits.

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
--qfa-geste-vente: #d1b781; /* GroupeAction.couleur, cf. Q4 */
--qfa-geste-loc: #ce614a; /* pink-tuile-main-556 */
--qfa-geste-tri: #a558a0; /* purple-glycine-main-494 */
```

Les SVG exportés du Figma servent de **masques CSS** plutôt que d'images : la
forme reste exactement celle de la maquette, et la couleur continue de venir
de `--qfa-pinpoint-couleur`, donc du geste choisi par l'usager (#3295).

> ⚠️ Parcel refuse une `url()` relative dans une custom property : elle se
> résout là où le `var()` est utilisé, pas là où il est défini. Les masques
> sont donc écrits directement dans `mask-image`, jamais via une variable.

## Deux écarts constatés, désormais tranchés

Les deux ont été arbitrés depuis, en [ADR 0009](0009-questions-a-trancher.md) :
**la base fait foi** pour la couleur (Q4), et **« Mauvais état »** est le
libellé retenu (Q5).

**1. `vendre_acheter` diverge.** Quatre des cinq couleurs correspondent déjà à
`GroupeAction.couleur` en base, ce qui confirme que le Figma est la source de
ces valeurs. La cinquième non :

| Code                        | En base          | Figma     |
| --------------------------- | ---------------- | --------- |
| `reparer`                   | `#009081`        | `#009081` |
| `donner_echanger_rapporter` | `#417dc4`        | `#417DC4` |
| `emprunter_preter_louer`    | `#ce614a`        | `#CE614A` |
| `vendre_acheter`            | **`#D1B781`** ✅ | `#BB8568` |
| `trier`                     | `#A558A0`        | `#A558A0` |

Le jeton Figma s'appelle `brown-caramel-sun-425-hover` : un jeton d'**état de
survol**, vraisemblablement prélevé par erreur sur un composant survolé.
**Tranché → la base fait foi** ([Q4](0009-questions-a-trancher.md)) : les cinq
couleurs viennent désormais de `GroupeAction.couleur`, une seule source pour
l'assistant et la carte historique.

**2. La spec et le Figma se contredisent sur un libellé.** #3295 décrit
« Prêter/Louer = orange » ; le Figma utilise `pink-tuile` (#CE614A), un
terracotta. La maquette fait foi, la spec décrit une intention.

## La typographie reste ouverte

Le composant « Barre de recherche » (nœud `24417:448`) est en **Public Sans**,
alors que la page des pinpoints est en **Marianne**. Marianne est déjà
embarquée via le DSFR ; Public Sans ne l'est pas.

Comme [ADR 0001](0001-pas-de-dsfr.md) écarte le DSFR de l'assistant, s'appuyer
sur Marianne aurait maintenu une dépendance discrète à ce paquet. **Tranché →
Public Sans, auto-hébergée** ([Q7](0009-questions-a-trancher.md)), sans appel à
Google Fonts.

## Conséquences

- Les pinpoints sont conformes à la maquette, vérifié au rendu.
- Un changement de couleur de geste se fait en un endroit.
- **Les assets sont copiés, pas liés** : une évolution du Figma ne se propage
  pas toute seule. C'est le prix d'un rendu qui ne dépend pas du réseau.
- Les jetons de dimension sont désormais repris : l'échelle d'espacement
  (`--qfa-espace-1v` à `-4v`, un pas de 4 px) et les deux rayons du Figma
  (`--qfa-rayon-sm: 4px`, `--qfa-rayon-md: 8px`) remplacent le `--qfa-rayon`
  approximé, conservé comme alias du rayon moyen.
- Les libellés courts des gestes ont désormais leur champ,
  `GroupeAction.libelle_court`, distinct de `libelle` qui reste une phrase
  ([Q6](0009-questions-a-trancher.md)).

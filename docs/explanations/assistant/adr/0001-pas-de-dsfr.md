# Décision 0001 : ne pas utiliser le DSFR dans l'assistant V2

Date : 2026-09-12

## Statut

Proposé

## Contexte

- Le reste du projet (carte, formulaire, assistant V1) charge le
  [DSFR](https://www.systeme-de-design.gouv.fr/) via `{% dsfr_css %}` et
  `{% dsfr_js %}`, et utilise ses composants (`fr-alert`, `fr-accordion`,
  `fr-btn`…).
- L'assistant V2 dispose de son **propre design system** :
  [« Composants spécifiques à Que faire »](https://www.figma.com/design/NxDiBpwtQxznMYJONS5nzk/),
  qui définit ses propres couleurs de geste, pinpoints, badges et blocs.
- Aucun composant Figma de l'assistant V2 ne correspond à un composant DSFR
  tel quel : tous seraient à surcharger.
- L'assistant est destiné à être **embarqué en iframe** chez des réutilisateurs
  (collectivités, e-commerçants, médias), où le poids transféré compte
  directement.
- Le ticket de cadrage ([#3434](https://app.notion.com/p/3d86523d57d780cda740c44ed0226417))
  précise : « pas besoin de SEO donc pas trop besoin de meta etc, se cantonner
  à ce qui est utile pour l'accessibilité ».

## Décision

L'assistant V2 **ne charge ni le CSS ni le JS du DSFR**. Il définit ses propres
composants sous le préfixe `qfa-`, à partir des tokens du Figma.

Les rares éléments que le DSFR fournissait gratuitement sont réimplémentés :

| Élément DSFR           | Remplacement                                  |
| ---------------------- | --------------------------------------------- |
| `{% dsfr_skiplinks %}` | `<a class="qfa-skiplink">` + ~6 lignes de CSS |
| `fr-accordion`         | `<details>` / `<summary>` natifs              |
| `fr-btn`               | `.qfa-bouton`                                 |
| `fr-alert`             | `.qfa-alerte`                                 |

## Conséquences

### Positives

- Les composants correspondent exactement au Figma, sans lutte contre des
  styles par défaut à surcharger.
- Pas de dépendance à la cadence de versions du DSFR pour cet écran.
- Le préfixe `qfa-` ne peut pas collisionner avec `fr-` ni `qf-`.
- Gain CSS réel : **mesuré à ~38 kb gzip** pour `quefaire.css` aujourd'hui
  (297 kb bruts). C'est le plafond de ce qu'on peut économiser côté CSS — et
  c'est **dix fois moins** que le gain obtenu en sortant MapLibre du bundle
  initial (voir [04-stimulus](../04-stimulus.md), section « Budget frontend »).
  **Le poids n'est donc pas le bon argument pour cette décision** ; la
  cohérence avec le design system l'est.

### Négatives

- **~100 lignes de CSS à écrire** pour ce que le DSFR fournissait.
- L'accessibilité n'est plus fournie par défaut : skiplink, focus visible,
  contrastes et navigation clavier deviennent notre responsabilité explicite.
  C'est le coût réel de cette décision, et il est assumé par des tests dédiés
  (voir [07-tests](../07-tests-et-qualite.md), section « Accessibilité »).
- L'assistant V2 diverge visuellement du reste du projet tant que la migration
  vers le nouveau design system n'est pas généralisée.

### Neutres

- Si le design system « Que faire » venait à s'aligner sur le DSFR, cette
  décision serait à reconsidérer — le préfixe `qfa-` isole suffisamment pour
  que ce soit faisable.

## Précision importante : Tailwind reste couplé au DSFR

⚠️ **Vérifié dans `webapp/tailwind.config.js`** : « ne pas charger le DSFR » ne
signifie pas « se passer de tout ce qui vient du DSFR ». La configuration
Tailwind du projet est **dérivée du DSFR** :

| Élément Tailwind                          | Origine                                                    |
| ----------------------------------------- | ---------------------------------------------------------- |
| `theme.colors`                            | `dsfr_hacks/colors` (palette DSFR complète)                |
| `theme.spacing` (`1v`, `1w`, `2w`…)       | échelle d'espacement DSFR                                  |
| plugin typographie (`fr-h1`…`fr-text--*`) | extrait de `@gouvfr/dsfr/dist/core/core.main.css` au build |
| utilitaires `qf-bg-*` / `qf-text-*`       | `dsfr_hacks/semantic_colors`                               |

Deux options, **à trancher en PR 1** :

1. **Garder la config Tailwind telle quelle** (recommandé pour démarrer) :
   l'assistant utilise `qf-` pour la mise en page et `qfa-` pour ses composants
   propres. On ne charge pas le CSS du DSFR, mais on hérite de son échelle
   d'espacement et de sa palette — ce qui est cohérent pour un service public.
2. **Config Tailwind dédiée à l'assistant**, avec les tokens du Figma
   uniquement. Plus pur, mais impose un second build Parcel/Tailwind et fait
   diverger deux échelles d'espacement dans le même dépôt.

Cette ADR ne tranche que le **chargement du CSS/JS DSFR** (`{% dsfr_css %}`,
`{% dsfr_js %}`, classes `fr-*` dans les templates de l'assistant). Elle ne
tranche pas la configuration Tailwind.

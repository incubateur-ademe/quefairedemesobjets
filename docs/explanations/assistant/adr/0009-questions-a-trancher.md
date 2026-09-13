# Décision 0009 : questions à trancher

Date : 2026-09-13

## Statut

**En attente** — ce document n'acte rien. Il consigne les questions ouvertes
rencontrées pendant l'écriture du plan, avec l'état de l'analyse, pour éviter
qu'un relecteur refasse le raisonnement à zéro.

Chaque question est close soit ici (réponse courte), soit par une ADR dédiée
qui la remplace. Une question tranchée est **retirée** de ce document et
remplacée par un lien.

| Question                                  | État                                 |
| ----------------------------------------- | ------------------------------------ |
| Q1 — marqueurs DOM ou couche MapLibre     | ouverte, penchant `Marker`           |
| Q2 — Tailwind sur l'assistant             | **tranchée** : retiré, −90 % de CSS  |
| Q3 — borner la distance en zone peu dotée | ouverte, arbitrage produit           |
| Q4 — couleur de `vendre_acheter`          | ouverte, arbitrage design            |
| Q5 — « Mauvais état » ou « Hors d'usage » | ouverte, arbitrage produit et design |
| Q6 — libellés courts des gestes           | ouverte, dépend de Q5                |
| Q7 — typographie de l'assistant           | ouverte, arbitrage design            |

Les questions tranchées sont conservées en place plutôt que retirées : leurs
réponses tiennent en quelques lignes, et ce qui les a tranchées — une mesure
pour Q2 et Q7, un arbitrage d'équipe pour Q4 à Q6 — vaut d'être gardé sous les
yeux.

Restent ouvertes : **Q1** (marqueurs DOM ou couche MapLibre) et **Q3** (borner
la distance en zone peu dotée), toutes deux issues du plan initial.

## Q1 — Marqueurs DOM ou couche MapLibre pour les points ?

**Contexte** : `#dessiner()` n'est spécifié nulle part dans
[04-stimulus](../04-stimulus.md). Le plan suppose partout des marqueurs DOM
(`import { Map, Marker }`, `anchor: "bottom"`, z-index CSS pour la punaise),
mais ne l'écrit jamais explicitement.

**État de l'analyse** :

| Critère                | `Marker` DOM                               | Couche `symbol` + `setData()`                 |
| ---------------------- | ------------------------------------------ | --------------------------------------------- |
| Perf à 20 points       | identique                                  | identique — le plafond tue l'argument         |
| Perf à ~500+ points    | dégrade (transform par frame)              | gagne                                         |
| 5 couleurs de pinpoint | CSS, une classe                            | atlas d'icônes (`addImage` × 5)               |
| Clic → Turbo Frame     | `<a href>`, gratuit                        | `queryRenderedFeatures` + navigation manuelle |
| Punaise au-dessus      | `z-index`                                  | couche séparée ordonnée                       |
| Coût de `#dessiner()`  | ~10 lignes de diff sur `Map<uuid, Marker>` | une ligne                                     |

**Penchant actuel** : rester sur `Marker`. La couche échange 10 lignes de diff
contre un atlas d'icônes et du hit-testing, pour un gain nul à 20 points.

**À rouvrir si** : `NOMBRE_MAX_LIEUX` dépasse ~500, ou si le plafond saute.

**Reste à faire quoi qu'il arrive** : spécifier `#dessiner()`. La règle « un
lieu sous les yeux de l'usager ne saute pas » (#3356) exige de **réutiliser
l'instance** des marqueurs conservés, pas de tout recréer — sinon le cache est
correct mais l'affichage clignote.

## ~~Q2 — Tailwind : préfixe et configuration dédiés pour l'assistant ?~~ — tranchée

**Réponse : ne pas utiliser Tailwind sur l'assistant** (option 3), et non
l'option 2 vers laquelle penchait l'analyse. C'est la mesure qui a tranché.

**Ce qui avait été supposé** : le sujet était un préfixe (`qfa-` contre `qf-`)
et une éventuelle directive `@config` par bundle, dont le support Parcel
restait à vérifier.

**Ce que la mesure montre** : le préfixe n'était pas le problème. En comptant
ce que `assistant.css` embarquait réellement :

| Mesure                                       | Valeur    |
| -------------------------------------------- | --------- |
| Classes `qf-` émises dans `assistant.css`    | **2 282** |
| Classes `qf-` réellement utilisées           | **1**     |
| Part du fichier occupée par des règles `qf-` | **81 %**  |

L'unique classe utilisée était `qf-scroll-smooth`, sur la balise `<html>` :
une ligne de CSS natif, qui faisait entrer tout l'utilitaire DSFR dans le
bundle.

**Effet du retrait des trois directives `@tailwind`** :

|          | Avant        | Après       |
| -------- | ------------ | ----------- |
| Brut     | 199 818 o    | 11 709 o    |
| **Gzip** | **25 139 o** | **2 650 o** |

Soit **−90 %**, pour un budget qui visait 30 kb. Rendu vérifié inchangé sur
les previews (étiquettes, badges, bloc geste, accordéon, footer) et sur la
carte (20 pinpoints, hauteur bornée) ; 30 tests pytest et 9 tests Jest verts.

**Pourquoi c'est cohérent** : [ADR 0001](0001-pas-de-dsfr.md) écarte le DSFR et
[ADR 0008](0008-jetons-de-design.md) donne des jetons relevés sur le Figma.
L'assistant avait donc déjà tout ce qu'il faut ; Tailwind n'apportait qu'un
vocabulaire concurrent, réglé sur une autre charte.

`scroll-behavior: smooth` est réécrit en CSS natif, et désormais neutralisé
sous `prefers-reduced-motion` — ce que l'utilitaire ne faisait pas.

**À rouvrir si** : l'assistant grossit au point que le CSS natif devient
difficile à tenir. Le préfixe `qfa-` reste disponible, et la question du
support de `@config` par Parcel redeviendrait alors ouverte — elle n'a pas été
tranchée, seulement rendue sans objet.

## Q3 — Faut-il borner la distance en zone peu dotée ?

**Contexte** : [ADR 0004](0004-tri-knn-sans-borne-de-distance.md) supprime toute
borne de distance et trie par l'opérateur KNN. Conséquence assumée : si un geste
n'est proposé nulle part à proximité, la requête renvoie quand même les 20 lieux
les plus proches, **fussent-ils à 300 km**.

La spec #3356 mentionne « un rayon de 20 km maximum ». L'implémentation ne le
respecte pas, délibérément.

**La question produit** : vaut-il mieux afficher un lieu lointain, ou ne rien
afficher et le dire ?

### Piste explorée : calculer une densité côté dbt

L'idée : une table dbt agrégeant la densité de lieux par maille (EPCI ou
grille), dont Django déduirait un rayon maximum adapté à la zone.

**Ce que ça ne résout pas** : la performance. Le rayon n'est plus un levier de
perf depuis l'ADR 0004 — on est à 2 ms à Paris, l'index GiST s'arrête au 20ᵉ
résultat. Une densité n'accélérerait rien ; elle réintroduirait même le
`ST_DWithin` que l'ADR 0004 a supprimé, et que son test de garde-fou interdit.

**Ce que ça pourrait résoudre** : la pertinence. Un seuil « au-delà de N fois la
distance médiane locale, n'affiche plus » est une règle de densité, et la
densité est bien un agrégat, donc un travail dbt légitime.

**Matériel déjà en place** — la maille existe, il n'y a rien à construire de
zéro :

- `int_epci` / `exposure_epci` : référentiel EPCI issu de `base_koumoul_epci` ;
- `marts_carte_acteur_epci`, `marts_opendata_acteur_epci`,
  `marts_exhaustive_acteur_epci` : les acteurs sont **déjà** rattachés à un
  EPCI par la macro `acteur_epci`.

Un modèle de densité serait donc un `GROUP BY code_epci` sur une table
existante, pas un nouveau pipeline.

**Objections à lever avant de s'engager** :

1. **La densité utile est par geste, pas globale.** « Réparer » et « donner »
   n'ont pas la même couverture : une densité agrégée tous gestes confondus ne
   répondrait pas à la question posée. La maille devient (EPCI × geste).
2. **L'EPCI est-il la bonne maille ?** Il est administratif, pas métrique : un
   EPCI rural est vaste et peu dense, un EPCI urbain petit et dense — ce qui
   joue plutôt en sa faveur. Mais un usager en bordure d'EPCI est mal servi par
   une règle calculée sur son seul EPCI.
3. **Le MVP en a-t-il besoin ?** Le cas dégénéré est déjà traité autrement par
   [ADR 0006](0006-strategie-adaptative-geste-objet.md). Une alternative sans
   data platform : mesurer la distance du 20ᵉ résultat **dans la requête**, et
   laisser le client décider de l'affichage. Pas de table, pas de
   synchronisation, pas de fraîcheur à gérer.

**Penchant actuel** : ne pas construire la densité pour le MVP. L'option
« distance du dernier résultat » répond à la même question sans nouvel objet.
La densité dbt devient intéressante si le produit veut une règle **stable et
explicable** (« dans votre EPCI, la couverture réparation est faible »), c'est
à dire un message, pas seulement un filtre.

**À trancher avec le produit avant d'aller plus loin** : afficher un lieu
lointain, ou afficher un message d'absence ? Tant que cette question n'est pas
répondue, construire une densité serait bâtir la mécanique d'une décision non
prise.

## ~~Q4 — Quelle couleur fait foi pour `vendre_acheter` ?~~ — tranchée

**Réponse : la base fait foi.** `--qfa-geste-vente` vaut `#D1B781`, la valeur
de `GroupeAction.couleur`, et non le `#BB8568` relevé sur le Figma.

L'indice qui allait dans ce sens : le jeton Figma était
`brown-caramel-sun-425-hover`, un jeton d'**état de survol** — vraisemblablement
pris par erreur sur un composant survolé dans la maquette.

Les cinq couleurs de geste viennent donc toutes de la base, ce qui aligne
l'assistant sur la carte historique : une seule source, une seule correction à
faire le jour où une couleur change.

> ⚠️ `gestes/geste-vendre.svg` avait la couleur **dans le fichier** (c'est une
> `background-image`, pas un masque) : son `fill` a été corrigé lui aussi. Les
> deux SVG de pinpoint gardent l'ancien `fill`, sans conséquence — servant de
> masques, seule leur forme est utilisée.

## ~~Q5 — « Mauvais état » ou « Hors d'usage » ?~~ — tranchée

**Réponse : « Mauvais état »**, le libellé du Figma.

La condition reste `mauvais_etat` côté code : le libellé est un paramètre du
gabarit, une reformulation ultérieure ne touchera pas au composant ni au CSS.

## ~~Q6 — Où vivent les libellés courts des gestes ?~~ — tranchée

**Réponse : un champ sur le modèle** (option 2). `GroupeAction.libelle_court`
porte le nom à l'infinitif affiché sur les étiquettes.

Migration `qfdmo/0192_groupe_action_libelle_court`, avec sa migration de données
qui renseigne les cinq groupes existants et sait se défaire (`RunPython` avec
son inverse).

| Champ           | Contenu                | Usage                    |
| --------------- | ---------------------- | ------------------------ |
| `libelle`       | « Je répare » (dérivé) | appel à l'action, phrase |
| `libelle_court` | « Réparer » (saisi)    | étiquette, badge, icône  |

Les deux coexistent volontairement : ce sont deux registres, pas une
redondance. La table Python qui servait de pis-aller dans
`previews/template_preview.py` a été supprimée — le libellé est désormais
éditable en admin, sans déploiement.

## ~~Q7 — Quelle typographie pour l'assistant ?~~ — tranchée

**Réponse : Public Sans, auto-hébergée.** Le Figma fait foi ; la police est
embarquée dans le dépôt, sans appel à Google Fonts.

**Mise en œuvre** : `@fontsource-variable/public-sans` (OFL-1.1), importé dans
`assistant.css` via le schéma `npm:` déjà utilisé par `dsfr.css`. Parcel copie
les `.woff2` à côté du CSS ; aucune URL externe ne subsiste dans le bundle
compilé, vérifié au grep et au trafic réseau.

**Ce que ça coûte** : le CSS passe de 2 650 à 3 055 o gzip (+405 o), et **un
seul** fichier de police part sur le réseau — `public-sans-latin-wght-normal`
(mesuré au chargement d'une preview). Trois raisons :

- **fonte variable** : un fichier couvre les graisses 400 à 700 utilisées par
  les composants, au lieu de quatre fichiers statiques ;
- **`unicode-range`** : les sous-ensembles latin-ext et vietnamien sont
  déclarés mais jamais téléchargés par une page française ;
- **italiques non importées**, faute d'usage dans les maquettes.

`font-display: swap` vient du paquet : le texte s'affiche immédiatement dans la
police de repli, puis bascule. Pas d'écran vide pendant le chargement.

**Pourquoi pas Marianne** : elle est disponible, mais seulement _via_ le DSFR,
que [ADR 0001](0001-pas-de-dsfr.md) écarte. S'appuyer dessus aurait maintenu
une dépendance discrète au paquet qu'on cherche à ne pas charger.

**Conséquence** : la page des pinpoints du Figma est en Marianne, l'assistant
en Public Sans. L'écart est dans la maquette, pas dans le code.

## Note — deux copies de MapLibre dans l'arbre npm

Consigné ici parce que ce n'est pas une question ouverte mais un correctif, et
qu'il touche la carte.

`webapp/package.json` déclarait `maplibre-gl: ^6.6.0`, alors que `carte-facile`
exige `^5.0.0`. npm installait donc **deux** copies : 5.24.0 pour carte-facile,
6.8.0 pour l'application. Les types divergeaient (`FontFacesSpecification`
n'est pas compatible entre les deux majeures) et `mapStyles.desaturated`
produisait un objet refusé par le constructeur typé en 6.x.

Le symptôme avait été traité une première fois en supprimant
`webapp/node_modules` — ce qui masquait la cause : le moindre `npm install` le
faisait revenir. La déclaration est désormais alignée sur `^5.24.0`, et
`npm ls maplibre-gl` ne montre plus qu'une seule version, dédupliquée.

> ⚠️ `webapp/tsconfig.json` n'a ni `include` ni `skipLibCheck`, et son
> `types: ["jest", "node"]` exclut `geojson`. `tsc` parcourt donc tout
> `node_modules` et signale des erreurs dans les `.d.ts` de dépendances
> (`@maplibre/geojson-vt`). Antérieur à ce travail, sans effet sur le build
> Parcel qui, lui, passe. À traiter séparément.

## Voir aussi

- [ADR 0004](0004-tri-knn-sans-borne-de-distance.md) — suppression de la borne de distance
- [ADR 0006](0006-strategie-adaptative-geste-objet.md) — cas où aucun lieu n'existe
- [ADR 0001](0001-pas-de-dsfr.md) — abandon du DSFR
- [ADR 0008](0008-jetons-de-design.md) — jetons de design, d'où viennent Q4 et Q7

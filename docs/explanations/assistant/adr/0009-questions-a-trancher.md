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

Q2 est conservée en place plutôt que retirée : sa réponse tient en quelques
lignes et la mesure qui l'a tranchée vaut d'être gardée sous les yeux.

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

## Q4 — Quelle couleur fait foi pour `vendre_acheter` ?

**Contexte** : les couleurs de geste ont été relevées sur le Figma (nœud
`368:1591`) pendant l'implémentation des pinpoints. Quatre des cinq
correspondent **exactement** à `GroupeAction.couleur` en base, ce qui indique
que le Figma est bien la source de ces valeurs. La cinquième diverge.

| Code                        | En base   | Figma     |            |
| --------------------------- | --------- | --------- | ---------- |
| `reparer`                   | `#009081` | `#009081` | ✅         |
| `donner_echanger_rapporter` | `#417dc4` | `#417DC4` | ✅         |
| `emprunter_preter_louer`    | `#ce614a` | `#CE614A` | ✅         |
| `vendre_acheter`            | `#D1B781` | `#BB8568` | ⚠️ diverge |
| `trier`                     | `#A558A0` | `#A558A0` | ✅         |

Le jeton Figma est `brown-caramel-sun-425-hover` — un jeton **`-hover`**, ce
qui peut signaler soit un choix délibéré, soit une teinte prise par erreur sur
un état de survol dans la maquette.

**État actuel** : la carte et les composants utilisent la valeur du Figma
(`#BB8568`). Les deux valeurs sont des bruns proches ; l'écart se voit sur un
aplat, pas sur une icône de 20 px.

**Ce qui dépend de la réponse** : la base sert aussi la carte historique. Si
c'est le Figma qui a raison, corriger `GroupeAction.couleur` aligne les deux
surfaces d'un coup ; si c'est la base, il faut corriger l'assistant **et** la
maquette, sinon l'écart reviendra au prochain relevé.

**À trancher avec le design.** Ce n'est pas une décision technique : les deux
valeurs fonctionnent.

## Q5 — « Mauvais état » ou « Hors d'usage » ?

**Contexte** : le composant badge affiche l'état d'un objet. La spec #3295
liste `Réparable`, `En bon état`, `Hors d'usage`. Le Figma (nœud `24381:25`)
nomme la troisième variante **« Mauvais état »**.

**État actuel** : le libellé est un paramètre du gabarit, la condition
(`mauvais_etat`) reste stable. Les deux formulations sont donc possibles sans
retoucher le composant, et la preview lookbook affiche celle du Figma.

**Pourquoi ce n'est pas qu'un détail** : les deux ne disent pas la même chose à
l'usager. « Hors d'usage » est un constat sur l'objet ; « mauvais état »
suggère un jugement, et laisse penser qu'une réparation reste envisageable —
alors que c'est précisément la branche où l'on oriente vers le dépôt.

**Penchant actuel** : suivre la spec (« Hors d'usage »), parce qu'elle décrit
l'intention produit, alors que le Figma fige une formulation.

**À trancher avec le produit et le design**, en même temps que Q6 : c'est le
même sujet de vocabulaire.

## Q6 — Où vivent les libellés courts des gestes ?

**Contexte** : le Figma étiquette les gestes à l'infinitif (« Réparer »,
« Donner », « Prêter », « Vendre », « Déposer »). `GroupeAction` n'a pas de
champ pour cela : sa propriété `libelle` rend une phrase à la première
personne — « Je répare », « Je dépose en point de collecte ».

Ce sont deux libellés pour deux usages, pas une redondance : la phrase sert un
appel à l'action, l'infinitif sert une étiquette.

**État actuel** : une table `LIBELLES_COURTS` dans `previews/template_preview.py`
fait la correspondance code → infinitif. C'est **volontairement un pis-aller** :
la table est dans les previews, donc invisible pour le reste de l'application.

**Options** :

| #   | Option                                     | Coût        | Conséquence                                         |
| --- | ------------------------------------------ | ----------- | --------------------------------------------------- |
| 1   | Garder la table Python                     | nul         | le libellé ne se change pas sans déploiement        |
| 2   | Ajouter `libelle_court` sur `GroupeAction` | migration S | éditable en admin, cohérent avec `libelle` existant |
| 3   | Le déduire de `libelle`                    | nul         | fragile : « Je dépose en point de collecte » → ?    |

L'option 3 ne tient pas : aucune règle ne transforme « Je dépose en point de
collecte » en « Déposer ».

**Penchant actuel** : option 2 si le produit veut pouvoir ajuster ces mots sans
dev — ce qui est probable vu Q5. Sinon l'option 1 suffit, à condition de
**sortir la table des previews** pour la mettre près du modèle.

**Dépend de Q5** : inutile de migrer avant que le vocabulaire soit arrêté.

## Q7 — Quelle typographie pour l'assistant ?

**Contexte** : le Figma utilise **Public Sans** sur les composants de
l'assistant (relevé sur `24417:448`, `24382:53`, `24414:395` — taille, graisse
et interlignage sont tous exprimés dans cette famille). La page des pinpoints,
plus ancienne, est en **Marianne**.

**Constaté** :

- Marianne est déjà embarquée par le DSFR, donc disponible sans rien ajouter ;
- Public Sans n'est **pas** dans le dépôt ;
- [ADR 0001](0001-pas-de-dsfr.md) écarte le DSFR de l'assistant — s'appuyer sur
  ses polices reviendrait à en garder une dépendance discrète.

**État actuel** : l'assistant ne déclare **aucune** `font-family`. Il hérite
donc de la police par défaut du navigateur, ce qui n'est un choix ni dans un
sens ni dans l'autre — c'est un trou, pas une décision.

**Ce qui est en jeu** : Marianne est la police de l'État et porte une identité
institutionnelle ; Public Sans est neutre. Le choix est autant éditorial que
technique. Embarquer une famille supplémentaire coûte par ailleurs des octets
sur un budget qui vient d'être ramené à 2,6 kb gzip (Q2).

**À trancher avec le design** : le Figma fait-il foi (Public Sans, à embarquer),
ou l'assistant reste-t-il sur Marianne, déjà présente ?

## Voir aussi

- [ADR 0004](0004-tri-knn-sans-borne-de-distance.md) — suppression de la borne de distance
- [ADR 0006](0006-strategie-adaptative-geste-objet.md) — cas où aucun lieu n'existe
- [ADR 0001](0001-pas-de-dsfr.md) — abandon du DSFR
- [ADR 0008](0008-jetons-de-design.md) — jetons de design, d'où viennent Q4 et Q7

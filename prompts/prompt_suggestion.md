# Interface de revue des suggestions SOURCE — superutilisateurs

## Objectif

Remplacer, pour la revue des suggestions de type SOURCE, les écrans Django admin
de `SuggestionCohorte` / `SuggestionGroupe` / `SuggestionUnitaire`
(webapp/data/admin.py) par une application dédiée, hors DSFR, pensée pour
traiter des milliers de suggestions rapidement (clavier, actions de masse,
UI optimiste).

**Périmètre : uniquement les cohortes SOURCE**, c'est-à-dire
`type_action ∈ {SOURCE_AJOUT, SOURCE_MODIFICATION, SOURCE_SUPPRESSION}`.
Côté serveur, filtrer avec la liste de l'enum (factoriser la logique de
`SuggestionCohorte.is_source_type` dans un QuerySet / une constante), et non
avec un préfixe de chaîne. Attention : la valeur stockée en base pour
SOURCE_SUPPRESSION est `"SOURCE_SUPRESSION"` (avec une faute de frappe).

Les autres types restent gérés par l'admin Django pour l'instant, mais
l'architecture doit permettre de les ajouter plus tard (voir « Politique de
revue par type_action »).

L'admin Django reste en place

Référence d'inspiration (pas de reprise de code) : PR #3016.
On repart d'une page blanche.

## Démarche — une étape à la fois, validation explicite entre chaque

1. **Mockup** : maquette HTML statique cliquable (données factices réalistes
   tirées des modèles) pour les écrans 1, 2.1 et 2.2. Je valide avant de continuer.
2. **Spécification technique** :
   - contrat d'API complet (routes, méthodes, paramètres, schémas Pydantic
     d'entrée/sortie, codes d'erreur, pagination) ;
   - format des filtres (voir « Filtrage ») ;
   - migration des champs de traçabilité ;
   - arbre de composants React (responsabilité, props, état local / serveur) ;
   - composant Web Awesome utilisé pour chaque élément d'interface ;
   - stratégie de données (cache, invalidation, mises à jour optimistes, rollback) ;
   - politique de revue de chaque sous-type SOURCE :
     - AJOUT : création d'acteur, il n'y a pas encore d'acteur existant à comparer ;
     - MODIFICATION : comparaison champ par champ ;
     - SUPPRESSION : Uniquement le champs statut est concerné par la mise à jour.
       Pour chacun, préciser ce qu'on affiche, ce qui est éditable et ce qui se
       valide ;
   - liste des questions ouvertes → **pose-les toutes avant de coder**.
3. **Implémentation**, en incréments livrables : socle (API + auth + page
   React vide), écran 1, écran 2.1, écran 2.2.
4. **Tests** : pytest unitaires + intégration sur l'API (`webapp/unit_tests/`,
   `webapp/integration_tests/`), tests de composants (jest, déjà configuré),
   e2e Playwright (`webapp/e2e_tests/`) sur un jeu de données déterministe
   créé par une commande de management dédiée.
5. **Documentation** : `docs/reference/webapp/suggestion_admin` (architecture,
   API, filtres, lancement en local). Ne pas toucher à `docs/changelog.md`.

## Architecture technique

- **API** : django-ninja, nouveau router monté sur `core/api.py`
  (ex. `/api/suggestions/`). Handlers fins, logique métier dans un module de
  services. Auth par session Django + CSRF ; **chaque route refuse tout
  utilisateur non `is_superuser` (403)**. Exposer le schéma OpenAPI et en
  générer les types TypeScript côté client.
- **Front** : React + TypeScript, point d'entrée Parcel séparé, chargé
  uniquement par une page Django `/data/revue/…` réservée aux superusers
  (le routage interne est côté client). Pas de DSFR.
- **UI** : Web Awesome (wrappers React) ; grille de données avec
  virtualisation (TanStack Table + Virtual ou équivalent) ; état serveur géré
  par une lib de type TanStack Query (optimistic updates + rollback).
- **Volume** : pagination par curseur, cohortes jusqu'à ~50k groupes.
- **Concurrence** : `select_for_update` sur les écritures de statut ;
  détection de conflit (via `modifie_le`) si deux superusers modifient le même
  groupe → erreur 409 et rafraîchissement de la ligne côté client.
- Après toute action, recalcul du statut du `SuggestionGroupe` puis de la `SuggestionCohorte`.

### Politique de revue par type_action

Les règles de revue (granularité de la validation, possibilité de refus,
champs affichés, éditabilité) sont regroupées dans une classe « politique »
par `type_action`, côté serveur, exposée au front par l'API. Le front lit
ces capacités et n'a aucune règle propre à un type en dur.
Seules les politiques SOURCE sont implémentées dans cette itération.

### Filtrage (sans DjangoQL)

Filtres structurés envoyés en JSON au serveur :
`{ "op": "and"|"or", "conditions": [ { "field", "operator", "value" } | groupe ] }`

- `field` : liste blanche définie côté serveur par écran ; les champs JSON
  (`metadata`, `contexte`, `parametres`) sont adressés par un chemin de clé
  (ex. `metadata.source_code`).
- `operator` selon le type : `eq`, `neq`, `contains`, `icontains`,
  `startswith`, `in`, `is_empty`, `is_not_empty`, `gt`, `lt`, `between`.
  **Pas de regex** (risque de ReDoS dans Postgres).
- Un endpoint « metadata de filtres » renvoie, pour chaque écran, les champs
  filtrables, leur type, leurs opérateurs et les valeurs possibles (choices,
  clés JSON connues) → alimente le constructeur de filtres React.
- Le même code serveur de filtrage sert à l'affichage ET aux actions de masse.
- L'état du filtre est sérialisé dans l'URL.
- Les filtres ne sont sensibles ni à la casse ni aux accents

### Traçabilité

Ajouter sur `SuggestionGroupe` et `SuggestionUnitaire` :

- `decision_par` : FK `User`, nullable, `on_delete=SET_NULL` ;
- `decision_le` : `DateTimeField`, nullable.

Ces champs sont renseignés à chaque décision humaine (validation → `ATRAITER`,
refus → `REJETEE`). L'annulation (undo) les remet à `NULL` en même temps
qu'elle restaure le statut précédent. Ils sont affichés dans les vues et
filtrables.

## Principes d'interface

- Pleine largeur, densité maximale, pas de gouttière ni d'espace perdu.
- Aucune action ne bloque l'interface : écriture optimiste, indicateur
  discret d'enregistrement, rollback + toast en cas d'erreur.
- Tout l'état de navigation (vue, filtres, tri, champs sélectionnés) est dans
  l'URL → partageable et restauré au rechargement.
- Navigation clavier par un **curseur unique** : ↑/↓ déplace le curseur ;
  A valide l'élément sous le curseur (groupe ou ligne) ; R refuse le groupe
  courant ; U annule ; ⏎ ouvre le détail ; Échap ferme ; `/` donne le focus
  au filtre. Après A ou R, le curseur passe à l'élément suivant pour enchaîner.

## Modèle de données et vocabulaire (à respecter strictement)

- `SuggestionCohorte` 1→N `SuggestionGroupe` 1→N `SuggestionUnitaire` (SU).
- Une SU porte `suggestion_modele`
  (`Acteur` | `RevisionActeur` | `ParentRevisionActeur`), `champs[]`, `valeurs[]`.
- **« Ligne de suggestion »** (unité affichée et validée) = pour un groupe
  donné, l'ensemble des SU qui portent sur le même tuple `champs`, tous
  modèles confondus. Ex. la ligne `(latitude, longitude)` regroupe les SU de
  ce tuple pour Acteur, RevisionActeur et ParentRevisionActeur.
  Valider une ligne = valider toutes les SU qui la composent.
- Statuts (`SuggestionStatut`) : `AVALIDER` → `ATRAITER` (validé) → `ENCOURS`
  → `SUCCES` | `ERREUR` ; `REJETEE`.

### Règles de la politique SOURCE

- **Tout le groupe ou rien** : une ligne ne peut pas être refusée isolément ;
  seul le groupe entier peut être refusé (`REJETEE`, avec toutes ses SU).
  L'API n'expose aucune route de refus de ligne pour ce type.
- Les lignes sont validées une par une ; le groupe passe automatiquement à
  `ATRAITER` quand toutes ses lignes sont validées. Valider le groupe valide
  toutes ses lignes restantes.
- La validation **ne fait que passer le statut à `ATRAITER`** ; l'application
  aux acteurs reste assurée par les tâches existantes, hors de cet écran.
- Seuls les éléments `AVALIDER` sont actionnables ; `ENCOURS`, `SUCCES` et
  `ERREUR` sont en lecture seule. Une annulation (undo) n'est possible que tant
  que l'élément est encore `ATRAITER` ou `REJETEE`.
- **Objets corrigeables** :
  - les SU sur `Acteur` reflètent la source et ne sont **jamais
    corrigeables** par l'utilisateur ;
  - seules les SU sur `RevisionActeur` et `ParentRevisionActeur` le sont ;
  - corriger un objet qui n'a pas encore de SU pour cette ligne crée cette
    SU, y compris quand l'acteur n'a pas encore de révision ;
  - **report** : la suggestion de l'Acteur peut être recopiée telle quelle
    dans la SU de la correction (▶, vers `RevisionActeur`) ou du parent (⏩,
    vers `ParentRevisionActeur`), ligne par ligne ou pour tout le groupe.
    C'est le comportement du contrôleur Stimulus `report-update` de l'admin
    (`target_values` = valeurs des SU Acteur). Un report crée ou met à jour la
    SU cible et ne valide pas la ligne ;
  - les champs non reportables
    (`SuggestionSourceModel.get_not_reportable_on_revision_fields` /
    `get_not_reportable_on_parent_fields`) ne sont pas corrigeables.
- Corriger une valeur réutilise la logique de `update_suggestion_groupe`
  (data/views.py) : mise à jour de la SU existante ou création d'une SU sur le
  bon modèle, avec validation `RevisionActeur.full_clean()`. Les erreurs de
  validation s'affichent sur le champ, sans bloquer le reste de l'écran. Une
  correction ne valide pas la ligne.

## Écrans

### 1. Liste des cohortes SOURCE

- Uniquement les cohortes SOURCE ayant au moins un groupe.
- `SuggestionCohorte` **n'a pas de champ `nom`** : aucune colonne ni aucun
  filtre « nom ». La cohorte est désignée par son id, son
  `identifiant_action` et la date d'exécution extraite de
  `identifiant_execution` (cf. `execution_datetime`).
- Colonnes : id, `identifiant_action` (avec la date d'exécution en dessous),
  `type_action`, `statut`, `identifiant_execution`, date de création,
  métadonnées (repliables), **compteurs de groupes par statut + barre de
  progression**.
- Filtres structurés sur tous les champs texte / JSON (dont les clés de
  `metadata`) + filtres rapides `type_action`, `statut`, période de création.
- Tri sur chaque colonne. Accès aux `SuggestionLog` de la cohorte (panneau latéral).
- Clic sur l'`identifiant_action` → écran 2.

### 2. Revue d'une cohorte — en-tête commun

id, `identifiant_action`, date d'exécution, type, compteurs, progression ;
bascule entre la vue **Groupes** et la vue **Lignes** (2.1 / 2.2) ; filtre de
visibilité commun :

- « À valider uniquement » (défaut) : groupes et lignes non validés ;
- « Groupes à valider, toutes leurs lignes » ;
- « Tout ».

Après une décision (validation ou refus, unitaire ou de masse) : les éléments
concernés sont marqués avec un toast « Annuler » pendant 10 s. L'écriture en
base est immédiate.

- Pour une action de masse, un seul toast annule toute l'action. Le serveur
  renvoie un identifiant d'opération ; l'annulation restaure, pour chaque
  élément touché, le statut précédent et `decision_par` / `decision_le`.
  Elle ignore les éléments qui ont changé entre-temps (déjà passés à
  `ENCOURS`, `SUCCES` ou `ERREUR`, ou modifiés par un autre utilisateur), et
  le toast de résultat indique combien d'éléments ont été restaurés et
  combien ont été ignorés.
- Ensuite, selon le filtre de visibilité, l'élément disparaît ou reste
  affiché avec son nouveau statut.

### Tableau des lignes de suggestion (commun à 2.1, 2.2 et à la modale de détail)

Reprendre au plus près la ligne de suggestion de l'admin Django
(`SuggestionSourceModel.to_comparison_table`, data/models/suggestions/source.py,
et les cellules `templates/data/_partials/cells/`). Une ligne de suggestion
(un tuple de `champs`) = **une ligne du tableau**, avec les colonnes :

| Champ(s) | Acteur importé | ▶   | Correction | ⏩  | Parent | Statut | Action |
| -------- | -------------- | --- | ---------- | --- | ------ | ------ | ------ |

- **Acteur importé** (`Acteur`) :
  - valeur actuelle de l'acteur et suggestion de la source pour ce champ ;
  - affichage en diff, comme `display_diff_values` : ancienne valeur barrée,
    nouvelle valeur en couleur ;
  - non corrigeable ;
  - pour un AJOUT, seule la valeur proposée est affichée (création).
- **▶** : reporte la suggestion de l'Acteur vers la Correction
  (`RevisionActeur`). Désactivé si un champ du tuple n'est pas reportable ou
  si la ligne n'est pas actionnable.
- **Correction** (`RevisionActeur`) :
  - valeur actuelle de la révision si elle existe (sinon « hérite de
    l'acteur » ou « pas de correction ») ;
  - modification proposée par la SU `RevisionActeur` si elle existe, en diff ;
  - corrigeable inline : met à jour la SU ou la crée.
- **⏩** : reporte la suggestion de l'Acteur vers le Parent
  (`ParentRevisionActeur`). Affiché seulement si l'acteur a un parent.
- **Parent** (`ParentRevisionActeur`) :
  - valeur actuelle du parent si l'acteur en a un ;
  - modification proposée par la SU `ParentRevisionActeur` si elle existe,
    en diff ;
  - corrigeable inline. Sans parent : « pas de parent ».
- **Action** : « Valider la ligne ».
- Une SU créée ou modifiée par l'utilisateur, à la main ou par report, est
  signalée dans sa cellule.
- Sur la ligne d'en-tête du groupe :
  - « ▶ Tout reporter » et « ⏩ Tout reporter », pour toutes les lignes du
    groupe (équivalent des `header_action` de l'admin) ;
  - les liens admin « importé / corrigé / affiché / parent » ;
  - le nombre d'enfants impactés par le parent.

### 2.1. Vue par groupe

- **Pas de panneau maître/détail** : la vue est un flux pleine largeur où
  chaque groupe est affiché en entier, tout le temps.
- Chaque groupe commence par sa **ligne d'en-tête**, qui sert aussi de ligne
  de validation du groupe. Elle contient :
  - une case de sélection ;
  - l'id, le nom de l'acteur, son `identifiant_unique` et sa ville ;
  - les indicateurs parent / révision / nombre de SU ;
  - la progression des lignes (`n/N lignes`) et le statut ;
  - `decision_par` / `decision_le` ;
  - les boutons Acteur / Localisation / Annuaire entreprise (modales) ;
  - les boutons « Refuser le groupe » et « Valider le groupe ».
- Les lignes de suggestion du groupe viennent juste dessous (tableau commun
  ci-dessus), puis le groupe suivant.
- **Navigation ↑/↓** : en-tête du groupe → chacune de ses lignes → en-tête
  du groupe suivant, etc.
  - A sur un en-tête valide le groupe entier et place le curseur sur
    l'en-tête du groupe suivant.
  - A sur une ligne valide cette ligne et passe à l'élément suivant.
  - R refuse le groupe courant, quelle que soit la position du curseur.
  - On peut ainsi valider un groupe d'un coup ou ligne par ligne.
- Pour les groupes `SOURCE_SUPPRESSION`, l'en-tête rappelle depuis quand
  l'acteur est absent de la source.
- Filtres : statut, `has_parent`, `has_correction`, nombre de SU,
  « contient une SU sur le champ X », `decision_par`, `decision_le`,
  champs JSON du groupe.
- Les onglets actuels (Acteur affiché, Localisation avec carte et marqueurs
  déplaçables, Annuaire entreprise) s'ouvrent en **modales**. Déplacer le
  marqueur crée ou corrige la SU sur `ParentRevisionActeur` si l'acteur a un
  parent, sinon sur `RevisionActeur`.
- Sélection multiple (sur les en-têtes de groupe) + actions de masse
  (valider, refuser des groupes), y compris sur « tout le filtré (N) ».
- Liste virtualisée (hauteurs de lignes variables) et pagination par curseur.

### 2.2. Vue par ligne de suggestion (mode focus)

- Liste des lignes de suggestion de la cohorte (une ligne = groupe × tuple de
  champs), avec l'id du groupe, le nom et l'`identifiant_unique` de l'acteur
  pour le contexte, puis les colonnes du tableau commun (Acteur importé ▶ Correction ⏩ Parent).
- Filtre par tuple de champs, par valeur suggérée, par objet visé par une SU
  (`Acteur` / `RevisionActeur` / `ParentRevisionActeur`)
  (opérateurs ci-dessus, conditions ET/OU), ou une combinaison.
- Correction inline identique à 2.1 ; ⏎ ou clic sur l'id ouvre la modale de
  détail du groupe complet.
- Action de masse **Valider** sur la sélection cochée OU sur « tout le
  filtré (N) », avec exclusions possibles et confirmation affichant le
  nombre exact. Pas de refus dans cette vue (règle SOURCE) ; un raccourci
  « Refuser le groupe » est disponible depuis la modale de détail.
- Les validations ligne par ligne doivent être instantanées (optimistes,
  enchaînables au clavier).
- Une validation de masse peut faire passer de nombreux groupes à
  `ATRAITER` : les compteurs de l'en-tête se mettent à jour.

# Système de suggestion

**Statut : ❓ À approuver**

Cette proposition de modification de l'architecture pour faire évoluer le système de suggestion est un travail itératif. Il est donc nessaire de garder en tête la cibe et le moyen d'y aller.

## Existant et problématique

il existe les tables `dagrun` et `dagrunchange`:

- `dagrun` représente un ensemble de suggestions produit par l'execution d'un DAG airflow
- `dagrinchange` représente la suggestion de modification pour une ligne donnée

On a quelques problème de lisibilité des ces tables:

- les types des évenements sont imprécis et utilisé pour plusieurs propos, par exemple, `UPDATE_ACTOR` est utilisé pour des propositions de siretisation et de suppression de acteurs lors de l'ingestion de la source
- les types des évenements sont définis au niveau de chaque ligne, pour connaitre le type de
- si une ligne est problématique, aucune ligne n'est mise à jour
- on n'à pas de vu sur les DAG qui on réussi ou se sont terminés en erreur

## Proposition d'amélioration

### Base de données

- Renommage des tables : `dagrun` -> `suggestion_cohorte` , `dagrunchange` -> `suggestion_ligne`
- Écrire les champs en français comme le reste des tables de l'application
- Revu des statuts de `suggestion_cohorte` : à traiter, en cours de traitement, fini avec succès, fini avec succès partiel, fini en erreur
- Ajout d'un type d'évenement à `suggestion_cohorte` : source, enrichissement
- Ajout d'un sous-type d'évenement à `suggestion_cohorte` : source - ajout acteur, source - suppression acteur, source - modification acteur, enrichissement - déménagement…

### Interface

Si possible, utiliser l'interface d'administration de Django pour gérer les suggestions (cela devrait bien fonctionner au mons pour la partie `ingestion des sources`).

- Division des interfaces de validation :
  - `ingestion des sources` : nouvelles sources ou nouvelle version d'une source existante
  - `enrichissements` : fermetures, démenagements, enrichissement avec annuaire-entrprise, l'API BAN ou d'autres API
- Ajout de filtre sur le statut (à traiter est sélectionné par défaut)
- Ajout de la pagination
- permettre de cocher les suggestions et d'executer une action our l'ensemble

### Pipeline

- Le DAG de validation des cohortes doit intégrer la même architecture que les autres DAGs

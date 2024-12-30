# Ingestion des sources

## Étapes

1. Vérification de la configuration
1. Normalisation
1. Vérification de la données à ingérer normalisées
1. Comparaison avec les instances des acteurs en base de données pour déterminer les acteurs à modifier, créer ou supprimer

### Vérification de la configuration

### Normalisation

en sortie de normalisation, les données des acteurs sont très proches des données cibles:

- Les liens vers les autres tables sont représentés par les codes, i.e. les objets actions, sous-catégories, label, acteur_type, label sont représenté par leurs codes en liste ou valeur simple
- les données à ingérer sont comparable aux données en base de données

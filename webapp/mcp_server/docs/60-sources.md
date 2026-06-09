# Sources de données

Le jeu de données « Que Faire De Mes Objets et Déchets » agrège des
contributions de très nombreux partenaires (éco-organismes, collectivités,
associations, fédérations professionnelles…).

## Tool `list_sources`

Le serveur MCP expose ce mapping via le tool `list_sources`, qui interroge
le modèle Django `qfdmo.Source` et renvoie pour chaque source son `code`,
son `libelle` et son `url`. Filtre optionnel par sous-chaîne :

```text
list_sources(libelle_contains="CRAR")
```

Réponse :

```json
{
  "sources": [
    {
      "code": "crar_normandie",
      "libelle": "CRAR Normandie",
      "url": "https://crar-normandie.fr/"
    }
  ]
}
```

## Champ `paternite`

Chaque acteur renvoyé par `search_actors` / `find_circular_solution` contient
une colonne `paternite` qui liste les contributeurs ayant fourni l'information
pour cet acteur, par exemple :

```text
Que faire de mes objets et déchets | ADEME | CRAR Normandie
```

Pour chaque libellé **autre que** « Que faire de mes objets et déchets » et
« ADEME », appeler `list_sources(libelle_contains=<libelle>)` pour récupérer
l'URL et l'inclure dans la restitution.

**Important** : ce champ doit être restitué (ou résumé) à l'utilisateur quand
on présente un acteur, conformément à la licence **Etalab / CC-BY** du jeu
de données.

## Liste de référence (XLSX)

L'ADEME publie aussi la liste complète des sources dans un fichier XLSX :
<https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/metadata-attachments/Sources%20de%20donn%C3%A9es%20-%20Que%20Faire%20De%20Mes%20Objets%20Et%20D%C3%A9chets.xlsx>

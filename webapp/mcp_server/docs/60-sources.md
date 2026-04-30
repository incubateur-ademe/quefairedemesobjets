# Sources de données

Le jeu de données « Que Faire De Mes Objets et Déchets » agrège des
contributions de très nombreux partenaires (éco-organismes, collectivités,
associations, fédérations professionnelles…).

- **Liste complète des sources** (XLSX, mise à jour par l'ADEME) :
  <https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/metadata-attachments/Sources%20de%20donn%C3%A9es%20-%20Que%20Faire%20De%20Mes%20Objets%20Et%20D%C3%A9chets.xlsx>
- **Page publique du dataset** : <https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire>

## Champ `paternite`

Chaque ligne du jeu de données contient une colonne `paternite` qui liste les
contributeurs ayant fourni l'information pour cet acteur, par exemple :

```
Que faire de mes objets et déchets | ADEME | CRAR Normandie
```

**Important** : ce champ doit être restitué (ou résumé) à l'utilisateur quand
on présente un acteur, conformément à la licence **Etalab / CC-BY** du jeu
de données.

## Identifiant unique

Le champ `identifiant` (ex. `222dMMK2fP52fhyhjJcYMY`) est l'identifiant stable
d'un acteur. Il peut être utilisé comme clé pour retrouver l'acteur sur le
site grand public :

<https://longuevieauxobjets.ademe.fr>

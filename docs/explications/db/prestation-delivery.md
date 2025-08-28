# Lieu de prestation

le lieu de prestation est défini par accteur via le champ lieu_prestation :

- `Sur place` : généralement en boutique
- `À domicile` : chez l'utilisateur final
- `Sur place et à domicile` : les 2
- Pas renseigné : On n'a pas eu l'information, on considèrera ces acteurs comme ayant un lieu de prestation sur place

Quand l'acteur permet un service à domicile, il est nécessaire de définir le périmètre concerné par cette offre de service

le périmètre de est définit pas le modèle `PerimetreADomicile`

- soit un département est définit
- soit un perimètre kilométrique est définit, il est appliqué autour de la localisation de l'acteur à vol d'oiseau

On définira un perimètre par département ou par périmètre kilométrique. les périmètres sont cumulatifs

Ex : si un acteur intervient dans les départements 19 et 46 oou à 50 km à la ronde, l'acteur aura 3 `PerimetreADomicile` définis :

- perimètre departement = 19
- perimètre departement = 46
- perimètre kilometrique = 50

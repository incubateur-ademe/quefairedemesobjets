# Docmentation Technique

La documentation technique est entretenu dans le code, dans le dossier [docs](./docs)

Elle suit la convention [DATAXIS](https://diataxis.fr) et mets en application, tant que faire se peut, les guidelines de doc définit par [Google](https://developers.google.com/style)

## TLTR : Dataxis

On découpe la documentation en 4 parties:

- TUTORIELS : Apprentissage pas à pas de l'utilisation de l'outils, ex : installer l'application sur un poste de développeur [./tutoriels](./docs/tutoriels)
- COMMENT-FAIRE : Guide l'utilisateur pour résoudre un problème, ex : copie de la base de données de prod vers preprod ([./comment-faire](./docs/comment-faire))
- EXPLICATIONS : Description de comment ça marche et des prises de décision, ex : architecture des données Acteurs et de leur revision [./explications](./docs/explications))
- REFERENCE : Description technique, ex : Architecture du dossier `data` [./reference](./docs/reference)

## Spécificité de la documentation du projet

Pour tous affirmation dans la documentation, il est possible d'ajouter un `Statut` qui décrit si la décision est appliquée.

- ❓ À approuver : l'équipe technque doit approuver la documentation avant de l'appliquer
- 🔄 En cours d'application : la proposition a été adoptée, est doit être appliquée

Si aucun statut n'est précisé, la documentation est valide et appliquée.

Une documentation refusé par l'équipe sera supprimée

Chaque modification de code qui désapprouve la documentation doit faire l'objet d'une modification de la Doc qui doit être approuvé en réunion de développeurs ou directement via la PR.

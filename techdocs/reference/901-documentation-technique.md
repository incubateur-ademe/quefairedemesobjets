# Guide de la docmentation technique

La documentation technique est entretenu dans le code, dans le dossier [docs](./docs)

Elle suit la convention [DATAXIS](https://diataxis.fr) et mets en application, tant que faire se peut, les guidelines de doc définit par [Google](https://developers.google.com/style)

![Organisation de la doc selon diataxis](https://diataxis.fr/_images/diataxis.png)

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

## Publication

**Statut : ❓ À approuver**

La doc devra être propulsée par un librairie de publication de doc, à définir.

Candidats:

- Docsify (JS)
- Sphinx (python) - A priori, la solution préférée à ce jour

## Convention

**Statut : ❓ À approuver**

### Liens vers les fichiers

On fera attention d'utiliser les chemins complets vers les fichiers cibles pour une compatibilité de navigations dans les IDE tel que vscode et dans l'interface github.com. Parmi les chemin suivants, on n'autorisera que le format whitelisté (✅):

- `[chemin vers le README.md du dossier](./<dossier>/README.md)` ✅
- `[chemin vers le README.md du dossier](/<dossier>/README.md)` ❌
- `[chemin vers le README.md du dossier](./<dossier>/)` ❌
- `[chemin vers le README.md du dossier](/<dossier>/)` ❌

### Règles de nommage des fichiers dans un dossier

Pour garantir l'ordre d'apparission des fichiers dans la barre de défilement à gauche, on préfix le fichier par un nummero de 3 chiffres qui détermine l'ordre d'apparition dans le menu

On groupera les sujets grâce au chiffre des centaines, puis des dizaines, et enfin on ordonnera les sous rubriques dans la barre de défilement latérale par ordre croisant des nom de fichiers

Ex : dans le dossier REFERENCE

- 101-coding-guidelines.md : en 1xx, les règles générales
- 201-frontend.md : en 2xx les règles frontend
- 311-db-guidelines.md : en 3xx les règles de donnée, 31x relatif à la base de données
- 322-organisations-des-fichiers-data.md : 32x relatif à la plateforme data
- 901-documentation-technique.md : 9xx les règles de documentation, volontairement en 9xx pour qu'elle soient affichiée à la fin de la section

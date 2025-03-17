# Guide de la docmentation technique

La documentation technique est entretenue dans le code, dans le dossier [docs](./)

Elle suit la convention [DIATAXIS](https://diataxis.fr) et met en application, tant que faire se peut, les guidelines de documentation définies par [Google](https://developers.google.com/style)

![Organisation de la documentation selon diataxis](https://diataxis.fr/_images/diataxis.png)

## TL;PL : Diataxis

On découpe la documentation en 4 parties:

- TUTORIELS : Apprentissage pas à pas de l'utilisation de l'outil, ex : installer l'application sur un poste de développeur ([docs/tutoriels](../tutoriels/README.md))
- COMMENT-FAIRE : Guide l'utilisateur pour résoudre un problème, ex : copie de la base de données de prod vers preprod ([docs/comment-faire](../comment-faire/README.md))
- EXPLICATIONS : Description de comment ça marche et des prises de décision, ex : architecture des données Acteurs et de leur revision ([docs/explications](../explications/README.md)))
- REFERENCE : Description technique, ex : Architecture du dossier `data` ([docs/reference](../reference/README.md))

## Spécificité de la documentation du projet

Pour toute affirmation dans la documentation, il est possible d'ajouter un `Statut` qui décrit si la décision est appliquée.

- ❓ À approuver : l'équipe technique doit approuver la documentation avant de l'appliquer
- 🔄 En cours d'application : la proposition a été adoptée, et doit être appliquée pour tout futur développement

Si aucun statut n'est précisé, la documentation est valide et appliquée.

Une documentation refusée par l'équipe sera supprimée

Chaque modification de code qui désapprouve la documentation doit faire l'objet d'une modification de la documentation qui doit être approuvée en réunion de développeurs ou directement via la _pull request_.

## Publication

**Statut : ❓ À approuver**

La documentation devra être propulsée par une bibliothèque de publication de documentation, à définir.

Candidats:

- Docsify (JS)
- Sphinx (python) - A priori, la solution préférée à ce jour

## Convention

**Statut : ❓ À approuver**

### Liens vers les fichiers

On fera attention d'utiliser les chemins complets vers les fichiers cibles pour une compatibilité de navigations dans les éditeurs tels que vscode et dans l'interface github.com. Parmi les chemins suivants, on n'autorisera que le format whitelisté (✅):

- `[chemin vers le README.md du dossier](./<dossier>/README.md)` ✅
- `[chemin vers le README.md du dossier](/<dossier>/README.md)` ❌
- `[chemin vers le README.md du dossier](./<dossier>/)` ❌
- `[chemin vers le README.md du dossier](/<dossier>/)` ❌

### Règles de nommage des fichiers dans un dossier

Pour garantir l'ordre d'apparition des fichiers dans la barre de défilement à gauche, on préfixe le fichier par un numéro de 3 chiffres qui détermine l'ordre d'apparition dans le menu

On groupera les sujets grâce au chiffre des centaines, puis des dizaines, et enfin on ordonnera les sous rubriques dans la barre de défilement latérale par ordre croisant des noms de fichiers

Ex : dans le dossier REFERENCE

- 101-coding-guidelines.md : en 1xx, les règles générales
- 201-frontend.md : en 2xx les règles frontend
- 311-db-guidelines.md : en 3xx les règles de données, 31x relatif à la base de données
- 322-organisations-des-fichiers-data.md : 32x relatif à la plateforme data
- 901-documentation-technique.md : 9xx les règles de documentation, volontairement en 9xx pour qu'elle soient affichées à la fin de la section

# Codes d'action

Les actions correspondent aux **services** qu'un acteur de l'économie
circulaire propose. Dans le jeu de données ADEME, chaque action est une
**colonne** dont la valeur est la liste des sous-catégories d'objet
concernées (séparateur `|`).

| Code                 | Libellé            | Quand l'utiliser                                                                                                                                       |
| -------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `preter`             | Prêter             | L'utilisateur veut **prêter** un objet à un tiers (acteur de prêt entre particuliers, bibliothèque d'objets…).                                         |
| `emprunter`          | Emprunter          | L'utilisateur veut **emprunter gratuitement** un objet (bibliothèque d'objets, prêt entre particuliers).                                               |
| `louer`              | Louer              | L'utilisateur veut **louer** un objet (location payante).                                                                                              |
| `mettre en location` | Mettre en location | L'utilisateur veut **proposer un objet à la location** (acteur recevant des objets pour les louer ensuite).                                            |
| `reparer`            | Réparer            | L'utilisateur veut faire **réparer** un objet (atelier de réparation, repair café, réparateur professionnel).                                          |
| `rapporter`          | Rapporter          | L'utilisateur veut **rapporter / déposer** un objet en fin de vie pour qu'il soit valorisé (point de collecte, déchèterie, magasin reprenant l'objet). |
| `donner`             | Donner             | L'utilisateur veut **donner** un objet (ressourcerie, association…).                                                                                   |
| `echanger`           | Échanger           | L'utilisateur veut **échanger** un objet contre un autre (boîte à livres, gratiferia, troc…).                                                          |
| `acheter`            | Acheter            | L'utilisateur veut **acheter d'occasion** (boutique de seconde main, ressourcerie, friperie…).                                                         |
| `revendre`           | Revendre           | L'utilisateur veut **revendre** un objet (dépôt-vente, plateforme acceptant les revendeurs particuliers).                                              |
| `trier`              | Trier              | L'utilisateur veut **savoir comment trier** ce déchet (centre de tri, conseils par filière).                                                           |

## Notes

- Les codes utilisent le **français sans accent**.
- `mettre en location` contient un **espace** (pas un underscore).
- Plusieurs actions peuvent être pertinentes pour une même intention :
  pour « se débarrasser », essayer `rapporter` puis `donner` puis `trier`.
- Filtre type `qs` :
  - `qs=reparer:"velo"` → acteurs réparant les vélos
  - `qs=donner:"vetement"` → acteurs acceptant les dons de vêtements
  - `qs="mettre en location":"materiel_de_sport_hors_velo"` → acteurs proposant
    de mettre en location du matériel de sport

# Codes d'action

Les actions correspondent aux **services** qu'un acteur de l'économie
circulaire propose. Ce serveur MCP les expose via le tool `list_actions`,
optionnellement filtrable par mot-clé :

```text
list_actions(query="reparer")
```

| Code               | Libellé            | Quand l'utiliser                                                                                                                                       |
| ------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `preter`           | Prêter             | L'utilisateur veut **prêter** un objet à un tiers (acteur de prêt entre particuliers, bibliothèque d'objets…).                                         |
| `emprunter`        | Emprunter          | L'utilisateur veut **emprunter gratuitement** un objet (bibliothèque d'objets, prêt entre particuliers).                                               |
| `louer`            | Louer              | L'utilisateur veut **louer** un objet (location payante).                                                                                              |
| `mettreenlocation` | Mettre en location | L'utilisateur veut **proposer un objet à la location** (acteur recevant des objets pour les louer ensuite).                                            |
| `reparer`          | Réparer            | L'utilisateur veut faire **réparer** un objet (atelier de réparation, repair café, réparateur professionnel).                                          |
| `rapporter`        | Rapporter          | L'utilisateur veut **rapporter / déposer** un objet en fin de vie pour qu'il soit valorisé (point de collecte, déchèterie, magasin reprenant l'objet). |
| `donner`           | Donner             | L'utilisateur veut **donner** un objet (ressourcerie, association…).                                                                                   |
| `echanger`         | Échanger           | L'utilisateur veut **échanger** un objet contre un autre (boîte à livres, gratiferia, troc…).                                                          |
| `acheter`          | Acheter            | L'utilisateur veut **acheter d'occasion** (boutique de seconde main, ressourcerie, friperie…).                                                         |
| `revendre`         | Revendre           | L'utilisateur veut **revendre** un objet (dépôt-vente, plateforme acceptant les revendeurs particuliers).                                              |
| `trier`            | Trier              | L'utilisateur veut **savoir comment trier** ce déchet (centre de tri, conseils par filière).                                                           |

## Notes

- Les codes utilisent le **français sans accent**.
- `mettreenlocation` ne contient pas d'**espace**.
- Plusieurs actions peuvent être pertinentes pour une même intention :
  pour « se débarrasser », essayer `rapporter` puis `donner` puis `trier`.
- C'est cette valeur qui est passée au paramètre `action` de `search_actors`
  ou `find_circular_solution`.

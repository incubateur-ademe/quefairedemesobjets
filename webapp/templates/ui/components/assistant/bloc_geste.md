# Bloc geste

Unité de la fiche objet : badges d'état, titre, consigne, appel à l'action.

## Utilisation

```django
{% include "ui/components/assistant/bloc_geste.html" with gestes=gestes libelle="Réparer" consigne=consigne badges=badges url=url %}
```

| Paramètre    | Rôle                                                             |
| ------------ | ---------------------------------------------------------------- |
| `gestes`     | codes des `GroupeAction` du bloc, une icône chacun               |
| `consigne`   | contenu CMS, **déjà marqué sûr en amont**                        |
| `badges`     | liste de `{condition, libelle}`                                  |
| `sans_carte` | vrai quand la fiche n'a pas de carte sur le site : pas de bouton |

L'ordre des blocs (réparable, bon état, hors d'usage) est décidé par la vue :
le bloc rend ce qu'on lui donne, dans l'ordre reçu.

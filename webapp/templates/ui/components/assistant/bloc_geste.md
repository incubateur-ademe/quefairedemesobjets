# Bloc geste

Unité de la fiche objet : badges d'état, titre, consigne, appel à l'action.

## Utilisation

```django
{% include "ui/components/assistant/bloc_geste.html" with geste="reparer" libelle="Réparer" consigne=consigne badges=badges url=url %}
```

| Paramètre      | Rôle                                                     |
| -------------- | -------------------------------------------------------- |
| `geste`        | code du `GroupeAction`                                   |
| `consigne`     | contenu CMS, **déjà marqué sûr en amont**                |
| `badges`       | liste de `{condition, libelle}`                          |
| `appel_action` | libellé du bouton (défaut « Je découvre les solutions ») |

## L'ordre n'est pas décidé ici

La priorité réparable → bon état → hors d'usage (#3295) est une règle métier :
elle appartient à la vue. Le bloc rend ce qu'on lui donne, dans l'ordre reçu.

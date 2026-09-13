# Badge

Étiquette d'état d'un objet, ou mise en avant du Bonus Réparation.

## Utilisation

```django
{% include "ui/components/assistant/badge.html" with condition="reparable" libelle="Réparable" %}
```

| `condition`    | Usage                               |
| -------------- | ----------------------------------- |
| `reparable`    | l'objet peut être réparé            |
| `bon_etat`     | l'objet fonctionne encore           |
| `mauvais_etat` | l'objet est hors d'usage            |
| `bonus`        | le lieu propose le Bonus Réparation |

Chaque condition associe un fond **et** une couleur de texte : les deux vont
ensemble, le contraste en dépend.

> ⚠️ Le Figma écrit « Mauvais état » là où la spec #3295 dit « Hors d'usage ».
> Le libellé étant passé en paramètre, le choix revient à l'appelant.

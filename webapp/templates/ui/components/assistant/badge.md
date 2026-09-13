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

Le libellé retenu est **« Mauvais état »**, celui du Figma, là où la spec #3295
écrivait « Hors d'usage » (tranché en ADR 0009, Q5). Le libellé reste un
paramètre : la condition `mauvais_etat` ne bouge pas si la formulation évolue.

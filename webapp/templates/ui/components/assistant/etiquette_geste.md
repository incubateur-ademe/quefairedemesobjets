# Étiquette de geste

Pastille qui nomme un geste, avec son icône et le fond pastel de sa famille.
Sert à qualifier un lieu sur sa fiche.

## Comment l'utiliser

```django
{% include "ui/components/assistant/etiquette_geste.html" with geste="reparer" libelle="Réparer" %}
```

| Paramètre | Rôle                                     |
| --------- | ---------------------------------------- |
| `geste`   | code du `GroupeAction`, porte la couleur |
| `libelle` | texte affiché, à l'infinitif             |

## Pourquoi le code plutôt que le libellé

La couleur est choisie à partir de `data-geste`, jamais du texte : un libellé
se reformule, un code non.

Le libellé vient de `GroupeAction.libelle_court`, un champ dédié : « Réparer ».
À ne pas confondre avec `GroupeAction.libelle`, qui rend une phrase à la
première personne (« Je répare ») déduite des actions du groupe. Les deux
coexistent, pour deux usages : l'étiquette et l'appel à l'action.

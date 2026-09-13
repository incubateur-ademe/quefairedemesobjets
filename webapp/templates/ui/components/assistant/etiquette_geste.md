# Étiquette de geste

Pastille qui nomme un geste, avec son icône et le fond pastel de sa famille.
Sert à qualifier un lieu sur la carte ou dans une fiche.

## Utilisation

```django
{% include "ui/components/assistant/etiquette_geste.html" with geste="reparer" libelle="Réparer" %}
```

| Paramètre | Rôle                                      |
| --------- | ----------------------------------------- |
| `geste`   | code du `GroupeAction` — porte la couleur |
| `libelle` | texte affiché, à l'infinitif              |

## Pourquoi le code plutôt que le libellé

La couleur est choisie à partir de `data-geste`, jamais du texte : un libellé
se reformule, un code non. C'est aussi ce qui permet à la carte et à la fiche
de rester cohérentes sans partager de gabarit.

> ⚠️ `GroupeAction.libelle` rend une phrase à la première personne (« Je
> répare »). Le Figma étiquette à l'infinitif. Les deux coexistent : ne pas
> remplacer l'un par l'autre.

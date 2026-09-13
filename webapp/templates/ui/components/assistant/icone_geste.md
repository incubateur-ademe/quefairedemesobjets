# Icône de geste

Pictogramme 24×24 d'un geste, à la couleur de sa famille.

## Utilisation

```django
{% include "ui/components/assistant/icone_geste.html" with geste="reparer" %}
```

Décorative par défaut (`aria-hidden`), parce qu'elle accompagne presque
toujours un libellé visible — l'annoncer deux fois dessert le lecteur d'écran.
Passer `titre` uniquement lorsqu'elle est seule porteuse de sens.

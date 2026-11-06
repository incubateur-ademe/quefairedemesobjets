# Accordéon

Section repliable, utilisée pour les horaires et les informations d'un lieu.

## Utilisation

```django
{% include "ui/components/assistant/accordeon.html" with intitule="Horaires" apercu=apercu contenu=contenu %}
```

| Paramètre  | Requis | Rôle                         |
| ---------- | ------ | ---------------------------- |
| `intitule` | ✅     | titre de l'accordéon         |
| `apercu`   | ⚪️     | résumé affiché une fois plié |
| `contenu`  | ✅     | contenu déplié               |
| `ouvert`   | ⚪️     | déplié dès l'affichage       |

## Pourquoi `<details>` et pas un contrôleur Stimulus

Le pliage, l'état ouvert/fermé, le rôle ARIA et la navigation clavier sont
natifs. Un contrôleur referait tout cela moins bien, et le contenu resterait
inaccessible sans JavaScript.

Le chevron pivote via `transform`, neutralisé sous `prefers-reduced-motion`.

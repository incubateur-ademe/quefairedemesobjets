# Pied de page

Lien « En savoir plus » et bloc de marques République française / ADEME /
Que faire de mes objets et déchets.

## Utilisation

```django
{% include "ui/components/assistant/footer.html" %}
```

## L'assistant vit en iframe

Le lien porte `target="_blank"` : sans lui, la page de destination s'ouvrirait
à l'intérieur du cadre, dans une fenêtre de quelques centaines de pixels.
`rel="noopener"` va avec, pour ne pas exposer la fenêtre parente.

Les logos sont des `<img>` avec `alt` et dimensions explicites : ce sont des
identités, pas des décorations, et les dimensions évitent un décalage au
chargement.

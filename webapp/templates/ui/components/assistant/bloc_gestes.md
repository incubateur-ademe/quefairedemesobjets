# Bloc gestes

Liste ordonnée des gestes possibles pour un objet.

## Utilisation

```django
{% include "ui/components/assistant/bloc_gestes.html" with blocs=blocs %}
```

Une `<ul>` plutôt qu'une suite d'`<article>` : le lecteur d'écran annonce le
nombre de gestes, et l'ordre porte du sens.

Sans aucun geste, le composant rend une alerte plutôt qu'un vide silencieux.

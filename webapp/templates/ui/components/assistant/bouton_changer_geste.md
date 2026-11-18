# Bouton « changer le geste »

Retour de l'écran solutions vers la fiche objet, en rappelant le geste actif.

## Comment l'utiliser

```django
{% include "ui/components/assistant/bouton_changer_geste.html" with libelle="Réparer" gestes=gestes url=url %}
```

`gestes` est facultatif : sans lui, pas d'icônes (retour de la fiche d'un lieu).

C'est un `<a>`, pas un `<button>` : la destination est une autre page. Un
bouton annoncerait une action sur place et casserait l'ouverture dans un
nouvel onglet.

Les icônes sont décoratives — le libellé porte déjà l'information.

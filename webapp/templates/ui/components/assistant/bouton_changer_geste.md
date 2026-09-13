# Bouton « changer le geste »

Retour de l'écran solutions vers la fiche objet, en rappelant le geste actif.

## Utilisation

```django
{% include "ui/components/assistant/bouton_changer_geste.html" with libelle="Réparer" gestes=gestes url=url %}
```

C'est un `<a>`, pas un `<button>` : la destination est une autre page. Un
bouton annoncerait une action sur place et casserait l'ouverture dans un
nouvel onglet.

Les icônes sont décoratives — le libellé porte déjà l'information.

# Composant Labels Acteur

Affiche les labels d'un acteur (Bonus, ESS, Répar'acteurs).

## Comment l'utiliser

```django
{% include "ui/components/carte/acteur/acteur_labels.html" with object=acteur %}
```

### Paramètres requis

- `object` : Objet DisplayedActeur avec labels

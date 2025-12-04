# Composant Mini Carte

Petit aperçu de carte montrant la localisation d'un acteur.

## Comment l'utiliser

```django
{% include "ui/components/mini_carte/mini_carte.html" with acteur=acteur_object location=point_object %}
```

### Paramètres requis

- `acteur` : Objet DisplayedActeur
- `location` : Objet géométrie Point (longitude, latitude)

### Paramètres optionnels

- `preview` : Booléen, mettre à True pour le mode prévisualisation
- `home` : Booléen, pour la variante page d'accueil

# En-tête Produit

En-tête principal pour les pages produit avec affichage optionnel du synonyme.

## Comment l'utiliser

```django
{# Utilisation basique #}
{% include "ui/components/produit/heading.html" with title="Mon produit" pronom="mon" %}

{# Avec synonyme #}
{% include "ui/components/produit/heading.html" with title="Mon produit" pronom="mon" synonyme="autre nom" %}
```

### Paramètres requis

- `title` : Le titre du produit
- `pronom` : Pronom possessif (mon, ma, mes)

### Paramètres optionnels

- `synonyme` : Nom alternatif pour le produit

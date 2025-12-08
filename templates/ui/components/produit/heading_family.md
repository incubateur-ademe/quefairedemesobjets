# En-tête Famille de Produits

En-tête pour les pages de famille de produits avec label de catégorie.

## Comment l'utiliser

```django
{% include "ui/components/produit/heading_family.html" with label="Catégorie" title="Mon produit" pronom="mon" %}
```

### Paramètres requis

- `label` : Label de catégorie
- `title` : Le titre du produit
- `pronom` : Pronom possessif (mon, ma, mes)

### Paramètres optionnels

- `synonyme` : Nom alternatif pour le produit

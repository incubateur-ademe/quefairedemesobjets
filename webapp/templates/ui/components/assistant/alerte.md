# Alerte

Encart d'information, par exemple un avertissement de tri propre à un objet.

## Utilisation

```django
{% include "ui/components/assistant/alerte.html" with message="Cet objet ne se jette pas avec les ordures ménagères." %}
```

## Accessibilité

`role="status"` et non `role="alert"` : le contenu est informatif et ne doit
pas interrompre la lecture en cours. `alert` est réservé à ce qui exige une
réaction immédiate.

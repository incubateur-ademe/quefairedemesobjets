# Composant Suggestions

Affiche une liste de suggestions avec liens.

## Comment l'utiliser

```django
{% include "ui/components/suggestions/suggestions.html" with heading="Titre" suggestions=suggestions_list %}
```

### Paramètres requis

- `heading` : Texte du titre de section
- `suggestions` : Liste de tuples (label, url)

### Exemple de contexte

```python
suggestions = [
    ("Suggestion 1", "/url1"),
    ("Suggestion 2", "/url2"),
]
```

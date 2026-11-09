# Panneau de recherche

Les deux champs de recherche du parcours : objet, puis adresse facultative.

## Comment l'utiliser

```django
{% include "ui/components/assistant/panneau_recherche.html" with bouton=True %}
```

| Paramètre  | Requis | Rôle                                                  |
| ---------- | ------ | ----------------------------------------------------- |
| `parcours` | ✅     | valeurs des champs, voir `assistant/parcours.py`      |
| `erreurs`  | ⚪️     | erreurs du formulaire de recherche                    |
| `bouton`   | ⚪️     | affiche « Lancer la recherche », inutile sur la fiche |

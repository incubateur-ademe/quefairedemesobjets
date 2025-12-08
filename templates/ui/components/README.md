# Documentation des Composants UI

Ce répertoire contient les composants UI réutilisables de l'application. Chaque composant a une documentation associée pour Django Lookbook.

## Comment Documenter les Composants

### Création de la Documentation

Pour chaque composant template `.html`, créez un fichier `.md` correspondant avec le même nom :

```
templates/ui/components/
├── button.html
├── button.md          ← Fichier de documentation
├── spinner.html
└── spinner.md         ← Fichier de documentation
```

### Format de Documentation

La documentation doit être concise et axée sur **comment utiliser** le composant. Utilisez ce modèle :

```markdown
# Nom du Composant

Brève description en une ligne.

## Comment l'utiliser

\`\`\`django
{% include "ui/components/path/to/component.html" with param1="value" param2="value" %}
\`\`\`

### Paramètres requis

- `param1` : Description

### Paramètres optionnels

- `param2` : Description (défaut : value)
```

### Directives

1. **Restez simple** - Concentrez-vous sur l'utilisation, pas les détails d'implémentation
2. **Templates Django uniquement** - Montrez la syntaxe des templates Django, pas le contexte Python
3. **Soyez concis** - Descriptions en une ligne, explications minimales
4. **Montrez des exemples** - Incluez des exemples d'utilisation réalistes

### Ajout aux Previews Django Lookbook

**Utilisez le décorateur `@component_docs`** pour charger automatiquement la documentation markdown :

```python
class ComponentsPreview(LookbookPreview):
    @component_docs("ui/components/my_component.md")
    def my_component(self, **kwargs):
        context = {"param": "value"}
        return render_to_string("ui/components/my_component.html", context)
```

Le décorateur automatiquement :

1. Cherche `templates/ui/components/my_component.md`
2. Lit le contenu markdown
3. L'injecte comme docstring de la méthode pour l'affichage dans Django Lookbook

**Pas besoin de docstring manuelle !** Créez simplement le fichier `.md` et ajoutez le décorateur `@component_docs`.

## Exemples

Voir les composants existants pour référence :

- `button.md` - Composant simple avec paramètres optionnels
- `spinner.md` - Composant avec variantes
- `produit/heading.md` - Composant avec plusieurs paramètres requis
- `icons/bonus.md` - Composant statique sans paramètres

## Système de Documentation Automatisé

### Décorateur `@component_docs`

Le décorateur `@component_docs(md_file_path)` dans `/previews/template_preview.py` charge automatiquement la documentation markdown depuis les fichiers `.md` :

```python
@component_docs("ui/components/button.md")
def button(self, **kwargs):
    context = {"href": "google.fr", "text": "test"}
    return render_to_string("ui/components/button.html", context)
```

Ceci remplace les docstrings manuelles et garantit que la documentation reste synchronisée avec les fichiers `.md`.

### Combinaison avec d'Autres Décorateurs

Le décorateur fonctionne avec d'autres décorateurs comme `@register_form_class` :

```python
@register_form_class(MyForm)
@component_docs("ui/components/my_component.md")
def my_component(self, **kwargs):
    # ...
```

**Important :** Placez `@component_docs` comme dernier décorateur (le plus proche de la fonction).

### Fonction Auxiliaire

La fonction sous-jacente `load_component_docs(template_path)` est disponible si vous avez besoin de charger programmatiquement la documentation markdown dans d'autres contextes.

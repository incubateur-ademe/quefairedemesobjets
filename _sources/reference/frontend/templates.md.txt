# Templates

## Organisation et découpage

On considère que le découpage de templates peut avoir lieu dans plusieurs situations :
- Rendre un **élément de design réutilisable** (composant du DSFR, composant custom)
- Rendre un **template moins lourd** et le découper en petites unités fonctionnelles

Un **template de composant** étant considéré comme réutilisable, il sera nommé `nom_du_composant.html`
Un **fragment de template** étant considéré local au template qu'il compose, il sera nommé `_nom_du_fragment.html` et placé dans un dossier portant le même nom que le template où il est utilisé.

L'organisation précise des templates est laissée au jugement du développement, mais l'idée est de faire remonter à proprement parler  au niveau le plus haut possible les fichiers de templates.
Par exemple, si on travaille sur le template de la fiche détaillée d'un acteur, qui utilise un composant tag, on peut retrouver l'arborescence suivante
```
shared
- tag.html
acteur
- fiche.html
- fiche
- - presentation.html
- - _tags.html
```

Avec par exemple
```jinja
{# _tags.html #}

{% for tag in tags %}
  {% include "shared/tag.html" %}
{% endfor %}
```

Note : cette convention a été adoptée en cours de projet et il est possible qu'une partie des templates legacy ne la respecte pas encore.
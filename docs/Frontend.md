# Frontend et templating

Le projet utilise le templating Django pour développer le frontend.

- Jinja vs templating Django
- Parcel
- Tailwind
- Organisation et découpage des templates
- Utilisation des formulaires
- Django DSFR

## Jinja et templating Django

Le projet utilise Jinja et le templating Django.
:warning: **Ces deux approches cohabitent mais il est envisagé d'abandonner Jinja à terme.**
Quand bien même les templates continuent d'être placé dans le dossier `jinja2` afin de garantir une rétrocompatibilité, tous les futurs développement doivent s'efforcer de s'affranchir de Jinja.

## Parcel

[Parcel](https://parceljs.org) est utilisé pour compiler les fichiers statiques : CSS, JS notamment.
Les sources sont configurées dans le fichier package.json`

### Transformers

Le projet utilise des _transformers_, ceux-ci sont principalement utilisés pour assainir le DSFR aujourd'hui.

### PostCSS

Parcel embarque PostCSS, celui-ci est étendu dans le projet pour supporter Tailwind et le [_CSS nesting_](https://www.w3.org/TR/css-nesting-1/)


## Organisation et découpage des templates

On considère que le découpage de templates peut avoir lieu dans plusieurs situations :
- Rendre un élément de design réutilisable (composant du DSFR, composant custom)
- Rendre un template moins lourd et le découper en petites unités fonctionnelles

Un template de composant étant considéré comme réutilisable, il sera nommé `nom_du_composant.html`
Un fragment de template étant considéré local au template qu'il compose, il sera nommé `_nom_du_fragment.html` et placé dans un dossier portant le même nom que le template où il est utilisé.

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

## Tailwind

Le projet utilise Tailwind.
Les classes Tailwind sont préfixées de `qfdmo` afin de les *namespacer* par rapport aux autres dépendances utilisées (DSFR notamment).

Afin de les rendre lisible, on tentera tant que possible de les grouper par usage sur une ligne.
Par exemple les classes relatives au style (bordure, couleur, taille de texte) pourront être distinguées de celles relative au positionnement.

```html
<div class="
  qf-flex qf-justify-around
  qf-border-solid qf-border-black qf-border-2
  qf-bg-white
">
```

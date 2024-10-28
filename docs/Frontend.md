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
Ces deux approches cohabitent mais il est envisagé d'abandonner Jinja à terme.
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

Un template de composant est nommé `_nom_du_composant.html`
Un template de fragment de template est nommé `nom_du_fragment.html`

Note : cette convention a été adoptée en cours de projet et il est possible qu'une partie des templates legacy ne la respecte pas encore.

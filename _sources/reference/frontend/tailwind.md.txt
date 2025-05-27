# Tailwind

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

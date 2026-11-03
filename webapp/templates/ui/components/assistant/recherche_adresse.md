# Recherche d'adresse

Champ de saisie d'adresse avec suggestions, en proxy devant la Base Adresse
Nationale.

## Utilisation

```django
{% include "ui/components/assistant/recherche_adresse.html" %}
```

## Ce que transportent les champs cachés

L'usager saisit du texte ; la carte a besoin de coordonnées. Choisir une
suggestion renseigne `longitude`, `latitude` et `precise`, que le formulaire
soumet ensuite.

`precise` distingue une adresse d'une commune : la punaise de l'adresse ne
s'affiche que pour la première, une commune n'ayant pas de position à montrer.

> ⚠️ Toute frappe ultérieure vide ces champs. Sans cela, corriger le texte sans
> re-choisir de suggestion soumettrait les coordonnées de l'adresse précédente.

## Trois caractères minimum

En deçà, la BAN ne renvoie rien d'exploitable : autant ne pas l'interroger.
Le champ « objet » s'ouvre lui dès deux caractères.

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

`precise` distingue une adresse d'une commune : la punaise rouge ne s'affiche
que pour la première. « Lyon » n'a pas de position à montrer (#3356), et son
centre géographique induirait l'usager en erreur.

> ⚠️ Toute frappe ultérieure vide ces champs. Sans cela, corriger le texte sans
> re-choisir de suggestion soumettrait les coordonnées de l'adresse précédente.

## Trois caractères minimum

En deçà, la BAN ne renvoie rien d'exploitable : autant ne pas l'interroger.
Le champ « objet » s'ouvre lui dès deux caractères.

## Géolocalisation

L'option « Autour de moi » de la carte historique n'est pas reprise : la
géolocalisation est hors périmètre MVP (#3295).

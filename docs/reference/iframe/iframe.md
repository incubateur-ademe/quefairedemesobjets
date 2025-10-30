# Iframe

Les paramètres d'Iframe ne concernent que l'Iframe de «La Carte»

## Les paramètres

les paramètres de l'iframe «CARTE» sont passés dans le dataset : en tant qu'attribut préfixé par `data-`

Les paramètres disponibles pour customiser l'affichage de l'iframe sont:

- `data-direction`, option `jai` ou `jecherche`, par défaut l'option de direction « Je cherche » est active
- `data-action_list`, liste des actions cochées selon la direction séparées par le caractère `|` :
  - pour la direction `jecherche` les actions possibles sont : `emprunter`, `echanger`, `louer`, `acheter`
  - pour la direction `jai` les actions possibles sont : `reparer`, `preter`, `donner`, `echanger`, `mettreenlocation`, `revendre`
  - si le paramètre `action_list` n'est pas renseigné ou est vide, toutes les actions éligibles à la direction sont cochées
- `data-max_width`, largeur maximum de l'iframe, la valeur par défaut est 800px
- `data-height`, hauteur allouée à l'iframe cette hauteur doit être de 700px minimum, la valeur par défaut est 100vh
- `data-iframe_attributes`, liste d'attributs au format JSON à ajouter à l'iframe

<!-- TODO : compléter avec tous les paramètres -->

La hauteur et la largeur de l'iframe peuvent être exprimées dans toutes les unités interprétées par les navigateurs ex: px, %, vh, rem…

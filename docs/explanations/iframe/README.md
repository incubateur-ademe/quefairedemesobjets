# Afficher l'application dans une Iframe

On affiche l'iframe grâce à un script JS.

## Script pour afficher «Que faire de mes objets/dechets ?»

```html
<script src="https://quefairedemesobjets.ademe.fr/iframe.js"></script>
```

## Script pour afficher «La Carte»

```html
<script
  src="https://quefairedemesdechets.ademe.fr/static/iframe.js"
  data-max_width="800"
  data-direction="jai"
  data-action_list="preter|donner|reparer|echanger|mettreenlocation|revendre"
></script>
```

Pour plus d'information sur les paramètres disponibles, utiliser les configurateurs ci-dessous ou la documentation technique du projet.

Voir l'exemple d'integration de l'iframe « Longue vie aux objets » dans une page html : [iframe.html](../../../iframe.html)

### Configurateur

2 configurateurs sont disponibles pour customiser l'integration de la carte

- Configurateur grand public : [https://longuevieauxobjets.ademe.fr/configurateur/](https://longuevieauxobjets.ademe.fr/configurateur/)
- Configurateur avancé (disponible uniquement pour les utilisateurs autorisés) : [https://quefairedemesobjets.ademe.fr/iframe/configurateur](https://quefairedemesobjets.ademe.fr/iframe/configurateur)

## Alternative d'intégration de l'application

Il est aussi possible d'intégrer directement l'iframe à votre site sans l'appel au script `iframe.js`. Dans ce cas, vous devrez passer les paramètres de l'iframe dans l'url (sans le préfix `data-`), configurer les appels à la librairie `iframe-resizer` et passer les bons attributs à l'iframe.

Vous trouverez un exemple d'intégration ici : [iframe_without_js.html](../../../iframe_without_js.html)

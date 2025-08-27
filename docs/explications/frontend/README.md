# 🎨 Frontend

```{toctree}
:hidden:

routing-nginx-cache.md
historique.md
```

Le projet dispose de deux frontend principaux

- **Longue Vie Aux Objets** : https://lvao.ademe.fr
- L'**assistant** : https://quefairedemesobjets.ademe.fr

Ils ont été développés en silo, et ne partagent à date qu'un minimum de code.
L'objectif à terme est d'en mutualiser une majeure partie au travers de refactorisations.

Longue vie aux objet est quant à lui découpé en deux briques fonctionnelles :

- Le **formulaire**, aussi appelé _version épargnons_
- La **carte**, intégrée au sein de l'assistant et par de nombreuses collectivités sous forme d'iframe
  Les différences sont [détaillées ici](https://www.notion.so/accelerateur-transition-ecologique-ademe/Sp-cifications-de-la-carte-170dcd6cdaee4a62b9f70c2040b363e2?pvs=4)

## Technologies employées

**Les technologies employées dans l'assistant sont à prendre comme référence pour l'intégralité des développements futurs sur le frontend**, à savoir :

- [**templating Django**](https://docs.djangoproject.com/en/5.1/topics/templates/)
- **Parcel** pour la compilation des fichiers JS/CSS
- **Tailwind**

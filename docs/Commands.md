# Commandes utiles

## En production

Pour executer une commande en production, il faut au préalable se connection au shell via le CLI Scalingo.
- [Installer le CLI](https://doc.scalingo.com/platform/cli/start)

Ensuite il est possible d'ouvrir un shell (ici bash) dans le worker Scalingo.

```
scalingo run --app quefairedemesobjets bash
```

À noter : remplacer `bash` par n'importe quelle commande ci-après est également possible, par exemple :

```
scalingo run --app quefairedemesobjets <nimporte-quelle-commande>
```

L'intégralité des commandes possibles n'est pas documentée ici, elle l'est dans la [documentation officielle de Django](https://docs.djangoproject.com/en/dev/ref/django-admin/#django-admin-and-manage-py)

### Créer un super-utilisateur

```
python manage.py createsuperuser
```

### Changer le mot de passe d'un utilisateur

```
python manage.py changepassword <nom-de-l-utilisateur>
```

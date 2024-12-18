# Commandes Django utiles

## En production

Pour executer une commande en production, il faut au préalable se connection au shell via le CLI Scalingo.
- [Installer le CLI](https://doc.scalingo.com/platform/cli/start)

Ensuite il est possible d'ouvrir un shell (ici bash) dans le worker Scalingo.

```sh
scalingo run --app quefairedemesobjets bash
```

L'intégralité des commandes possibles n'est pas documentée ici, elle l'est dans la [documentation officielle de Django](https://docs.djangoproject.com/en/dev/ref/django-admin/#django-admin-and-manage-py)

L'ensemble des commandes documentées ci-après peut être lancée soit depuis un environnement local, soit depuis un shell en production ou pré-production.

### Créer un super-utilisateur

```sh
python manage.py createsuperuser
```

### Changer le mot de passe d'un utilisateur

```sh
python manage.py changepassword <nom-de-l-utilisateur>
```

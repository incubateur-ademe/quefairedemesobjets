# Règle de codage de la base de données

## Gestion de valeurs par défaut dans la base de données

**Etat :** ❓ À approuver

Pour les champs de type string ne doivent pas être nullable, la valeur par défaut est une chaine vide comme indiqué dans la documentation de Django : [https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options](https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options)

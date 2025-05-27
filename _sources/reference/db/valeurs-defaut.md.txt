# Gestion de valeurs par défaut dans la base de données

## Chaînes de caractères

Pour les champs de type string ne doivent pas être nullable, la valeur par défaut est une chaine vide comme indiqué dans la documentation de Django : [https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options](https://docs.djangoproject.com/en/5.1/ref/models/fields/#field-options)

## Booleen

Les booléens peuvent avoir une valeur nulle, cela signifie qu'on n'a pas l'information

ex : uniquement_sur_rdv : True/False/None -> Oui/Non/Nous n'avons pas l'information

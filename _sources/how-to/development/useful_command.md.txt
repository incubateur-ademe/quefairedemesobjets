# Commandes Django utiles

## Créer un super-utilisateur

```sh
python manage.py createsuperuser
```

## Changer le mot de passe d'un utilisateur

```sh
python manage.py changepassword <nom-de-l-utilisateur>
```

## Création des liens entre bases de données

On utilise 2 bases de données par environnement. Chaque instance de bases de données est disponible sur l'autre base via un schema en utilisant le pluggin `postgres_fdw`

- sur la DB `warehouse`, la base de données `webapp` est dispponible via le schema `webapp_public`
- sur la DB `webapp`, la base de données `warehouse` est dispponible via le schema `warehouse_public`

Pour créer ou mettre à jour ces schemas, utiliser la commmande `create-remote-db-server` :

```sh
make create-remote-db-server
```

## Copier la base de données de prod en local

```sh
make db-restore-local-from-prod
```

## Copier la base de données de preprod en local

```sh
make db-restore-local-from-preprod
```

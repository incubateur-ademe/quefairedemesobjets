# Provisionner l'infrastructure

Cette configuration OpenTofu gère l'infrastructure de QueFaireDeMesObjets sur Scaleway.

## OpenTofu

Nous utilisons OpenTofu, version open-source de `Terraform`, pour automatiser le provisionning de l'infractructure. \
Suivre la documentation pour installer OpenTofu : https://opentofu.org/docs/intro/install/

La configuration est définie dans le dossier `infrastructure`

### Prérequis

Installer et configurer le client Scaleway en suivant [les instructions de Scaleway](https://www.scaleway.com/en/docs/scaleway-cli/quickstart/)

Vérifer que vous avez les droits d'administration du projet concerné par cette planificaton d'infrastructure

### IaC : Infrastructure as Code

#### Structure

```
infrastructure/
├── environments/
│   ├── prod/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars.exemple
│   │   └── terraform.tfvars -> non partagé
│   ├── preprod/
│   └── dev/
└── modules/
    ├── database/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── provider/
```

#### Configuration

1. Copier le fichier `environments/dev/terraform.tfvars.example` vers `terraform.tfvars`
2. Modifier les valeurs dans `terraform.tfvars` avec vos informations :
   - `project_id` : ID du projet Scaleway
   - `organization_id` : ID de l'organisation Scaleway
   - `db_password` : Mot de passe sécurisé pour la base de données
   - …

### Exécution

#### tfstate

⚠️ le `state` est enregistré sur une répertoire s3 de Scaleway s3://

Si ce répertoire n'existe pas, il est nécessaire d'executer la configuration `backend`, cf. [infrastructure/environments/backend](../../../infrastructure/environments/backend/)

#### Par environnement

Pour chaque environnement :

* [Preprod](../../../infrastructure/environments/preprod)
* [Prod](../../../infrastructure/environments/prod)z


Se placer dans le répertoire `infrastructure` et exécuter les commandes suivantes

```sh
tofu init -reconfigure
```

```sh
tofu plan
```

```sh
tofu apply
```

Pour chaque commande, l'environnement doit-être précisé

### Questions

Quelles sont les bonnes pratiques pour gérer les variables d'environnement ?

1. lesquelles sont publiques et publiables ? project_id ? organisation_id
2. lesquelles ne sont pas publiable ?
3. où mettre les variables (publiable : Node type, volume size…) vs les secrets (passwords, secrets…) ?

J'utilise le client scaleway (puisse que mon client scaleway est installé et provisionné), est-ce la bonne pratique ou est-ce qu'on doit avoir une config avec des access et secret keys ?

Comment organiser son infra, dispatche en dossiers selon les blocks fonctionnels

Comment faire une config qu'on applique en preprod et une autre en prod ?

Qu'est-ce qu'il faut mettre dans le .gitignore ? est-ce qu'on peut partager le .tfstate et comment ? ou est-ce qu'il faut toujour partir d'un init ?

Comment avoir un paramète requis, ici l'environnement pas exemple ?

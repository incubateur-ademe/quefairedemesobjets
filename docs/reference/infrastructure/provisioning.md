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
│   └── preview/
└── modules/
    ├── database/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── provider/
```

#### Configuration

1. Copier le fichier `environments/<ENV>/terraform.tfvars.example` vers `terraform.tfvars`
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

L'environnement de `preview` est utilisé pour tester notre projet IaC, on détruit volontairement l'infrastructure créée sur cet environnement une fois que la configuration terraform est testée.

Pour chaque environnement :

- [Preprod](../../../infrastructure/environments/preprod)
- [Prod](../../../infrastructure/environments/prod)

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

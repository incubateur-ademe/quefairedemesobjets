# Provisioning the infrastructure

This OpenTofu configuration manages the QueFaireDeMesObjets infrastructure on Scaleway.

## Scaleway

All resources on Scaleway are provisioned in the organization `Incubateur ADEME (Pathtech)` and the project `longuevieauxobjets`.

All resources are named following the pattern `lvao-{env}-{explicit-name}` (for example: `lvao-prod-webapp-db`).

## OpenTofu & Terragrunt

We use OpenTofu, the open-source version of `Terraform`, to automate infrastructure provisioning. [Follow the documentation](https://opentofu.org/docs/intro/install/) to install OpenTofu.

[Terragrunt](https://terragrunt.gruntwork.io/) is used alongside OpenTofu to keep the configuration DRY. [Follow the documentation](https://terragrunt.gruntwork.io/docs/getting-started/install/) to install Terragrunt.

The configuration is defined in the `infrastructure` directory.

### Prerequisites

Install and configure the Scaleway CLI by following [Scaleway's instructions](https://www.scaleway.com/en/docs/scaleway-cli/quickstart/).

Make sure you have administration rights on the project targeted by this infrastructure plan.

### IaC: Infrastructure as Code

#### Structure

```
infrastructure/
├── environments/
│   ├── prod/
│   │   ├── terragrunt.hcl
│   │   ├── terraform.tfvars.example
│   │   └── terraform.tfvars -> not versioned
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

1. Copy `environments/<ENV>/terraform.tfvars.example` to `terraform.tfvars`.
2. Edit the values in `terraform.tfvars` with your information:
   - `project_id`: Scaleway project ID
   - `organization_id`: Scaleway organization ID
   - `db_password`: secure password for the database
   - …

### Execution

#### tfstate

⚠️ The Terraform state is stored in a Scaleway S3 bucket: `s3://lvao-terraform-state`.

#### Per environment

The `preview` environment is used to test our IaC project. We intentionally destroy the infrastructure created in this environment once the Terraform configuration has been tested.

For each environment:

- **Preprod**: `infrastructure/environments/preprod` at the repository root
- **Prod**: `infrastructure/environments/prod` at the repository root

Change directory to `infrastructure/environments/<ENV>` and run:

```sh
terragrunt init -reconfigure --all
```

```sh
terragrunt plan --all
```

```sh
terragrunt apply --all
```

For each command, the environment must be specified.

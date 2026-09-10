# Rotating database passwords

Operational procedure to rotate the PostgreSQL passwords of an environment (`preprod` or `prod`).

The three managed RDB instances (`lvao-{env}-webapp`, `lvao-{env}-warehouse`, `lvao-{env}-airflow`) store their admin passwords in OpenTofu variables. Changing them requires a coordinated update of **every consumer**: Terragrunt, Scalingo, GitHub, and the password vault.

> **See also**: [Provisioning](../../reference/infrastructure/provisioning.md), [Secrets](../../reference/security/secrets.md), [Database organisation](../../reference/db/db_organisation.md), [PRA — secret compromise](../../reference/security/pra.md).

⚠️ **Expect a short outage.** As soon as the database stack is applied, the old passwords stop working. Update Airflow and Scalingo immediately afterwards. Prefer a maintenance window and announce it on Mattermost (`lvao-tour-de-controle`).

⚠️ **Never commit `terraform.tfvars`.** These files are gitignored. After the rotation, copy the updated values into [Vaultwarden](https://vaultwarden.incubateur.net) (see [Save the new secrets](#4-save-the-new-secrets)).

## 1. Prepare access

Confirm you can log in to every system involved **before** changing any password.

| Access                                         | Why it is needed                                                |
| ---------------------------------------------- | --------------------------------------------------------------- |
| **Scaleway** (console + CLI)                   | Apply OpenTofu, inspect RDB instances, check Airflow containers |
| **OpenTofu / Terragrunt**                      | Local `terraform.tfvars` for the target environment             |
| **Scalingo** (console + CLI)                   | Update webapp environment variables and restart the app         |
| **GitHub**                                     | Update repository / environment secrets used by CI              |
| **Airflow UI**                                 | Smoke-test the metadata database after the rotation             |
| **Vaultwarden** (`vaultwarden.incubateur.net`) | Persist the new `terraform.tfvars` values                       |

You also need administration rights on the Scaleway organisation `Incubateur ADEME (Pathtech)`, project `longuevieauxobjets`.

## 2. Change the passwords

### 2.1. Update `terraform.tfvars`

Edit the **non-versioned** file:

```text
infrastructure/environments/<ENV>/database/terraform.tfvars
```

Replace these three values with newly generated strong passwords:

| Variable                | Instance               | Admin user  |
| ----------------------- | ---------------------- | ----------- |
| `webapp_db_password`    | `lvao-{env}-webapp`    | `webapp`    |
| `warehouse_db_password` | `lvao-{env}-warehouse` | `warehouse` |
| `airflow_db_password`   | `lvao-{env}-airflow`   | `airflow`   |

This protocol does **not** rotate the read-only Metabase users (`webapp_db_metabase_password`, `warehouse_db_metabase_password`). Rotate those separately if needed, then update the Metabase connection settings.

When embedding a password in a DSN (`postgres://user:password@host:port/db`), avaid some reserved characters (`@`, `:`, `/`, `?`). Terragrunt interpolates the raw password into Airflow DSNs; Scalingo and GitHub store full URLs — encode consistently in every URL you write by hand. <!-- # pragma: allowlist secret -->

### 2.2. Apply the database stack, then Airflow

Apply **in this order**. The Airflow containers read the new passwords from the database module outputs.

From the repository root:

```sh
cd infrastructure/environments/<ENV>/database
terragrunt plan
terragrunt apply
```

This updates the RDB users on Scaleway and re-applies the `postgres_fdw` user mappings between `webapp` and `warehouse` (those mappings embed the same passwords).

Then:

```sh
cd ../airflow_containers
terragrunt plan
terragrunt apply
```

This refreshes the secret environment variables of the three Airflow containers (`webserver`, `scheduler`, `dag-processor`):

| Variable                              | Password it carries     |
| ------------------------------------- | ----------------------- |
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | `airflow_db_password`   |
| `AIRFLOW_METADATA_DB_URL`             | `airflow_db_password`   |
| `AIRFLOW_CONN_WEBAPP_DB`              | `webapp_db_password`    |
| `DATABASE_URL`                        | `webapp_db_password`    |
| `DB_WAREHOUSE`                        | `warehouse_db_password` |
| `POSTGRES_PASSWORD`                   | `warehouse_db_password` |

Review the plan before applying: you should see password / secret-env changes only, not instance recreation.

### 2.3. Update Scalingo and restart

The Django webapp (and its `worker`) still use the **old** passwords until Scalingo is updated.

On the Scalingo app of the target environment (production app: `quefairedemesobjets`; preprod app: `quefairedemesobjets-preprod`):

| Variable       | Points to              | Password                |
| -------------- | ---------------------- | ----------------------- |
| `DATABASE_URL` | `lvao-{env}-webapp`    | `webapp_db_password`    |
| `DB_WAREHOUSE` | `lvao-{env}-warehouse` | `warehouse_db_password` |

Example with the CLI (percent-encode the password inside the URL):

```sh
scalingo --app <SCALINGO_APP> env-set \
  DATABASE_URL='postgres://webapp:<ENCODED_PASSWORD>@<HOST>:<PORT>/webapp?sslmode=require' \
  DB_WAREHOUSE='postgres://warehouse:<ENCODED_PASSWORD>@<HOST>:<PORT>/warehouse?sslmode=require'

scalingo --app <SCALINGO_APP> restart
```

Keep host, port, user, and database name unchanged; only the password part of the URL changes. Restart is required so Gunicorn and the worker pick up the new values.

### 2.4. Update GitHub secrets

These secrets are used by CI to talk to the preprod webapp database (weekly prod → preprod sync and related restore scripts).

| Secret                  | Used by                                |
| ----------------------- | -------------------------------------- |
| `PREPROD_DATABASE_URL`  | `scripts/restore_prod_to_preprod.sh`   |
| `PREPROD_DB_WEBAPP_DSN` | `.github/workflows/sync_databases.yml` |

Update both with the new preprod `webapp` DSN (same value as Scalingo `DATABASE_URL` for preprod).

Location: GitHub → repository **Settings** → **Secrets and variables** → **Actions** (and the `preprod` environment if the secret lives there).

When rotating **production**, check the `prod` GitHub environment for any equivalent DSN secret before leaving the procedure.

## 3. Test

After restart, confirm that every surface that opens a database connection still works.

| Surface    | What to check                                                            |
| ---------- | ------------------------------------------------------------------------ |
| **Webapp** | Public map and assistant load and return results (search, acteur sheet). |
| **Admin**  | Sign in to Django Admin (`/admin/`) and open an acteur.                  |
| **CMS**    | Sign in to Wagtail (`/cms/`) and open a page.                            |

Recommended extras:

- Airflow UI loads and DAGs are visible (validates `airflow_db_password`).
- Sentry / Scaleway Cockpit: no burst of connection-authentication errors after the restart.

If a check fails, the usual cause is a consumer still using the old password, or a DSN that was not percent-encoded.

## 4. Save the new secrets

1. Update the Vaultwarden note(s) that store the environment `terraform.tfvars` on [vaultwarden.incubateur.net](https://vaultwarden.incubateur.net) with the new `webapp_db_password`, `warehouse_db_password`, and `airflow_db_password`.
2. Keep the local `terraform.tfvars` in sync with that note.
3. Do not paste the passwords in Mattermost, GitHub issues, or commit messages.

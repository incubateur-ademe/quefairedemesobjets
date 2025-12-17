# ☎️ 3615 jaidesproblemes

Une liste de solutions à des situations fréquentes qui peuvent se produire en local, en staging, en prod...

## git

### En cas de conflits sur `.secrets.baseline`

```bash
# installer detect-secrets s'il n'est pas présent dans l'environnement virtuel
# ou en local
uv add detect-secrets
# re-générer .secrets.baseline
uv run detect-secrets scan > .secrets.baseline
# ajout au rebase en cours
git add .secrets.baseline
# continuer le rebase si aucun autre conflit n'est présent
git rebase --continue
```

### En cas de conflits sur `uv.lock`

```bash
# ou avec uv
rm uv.lock
uv lock
git add uv.lock

# si c'est pendant un rebase...
git rebase --continue
```

## Mise en place du poste developpeur

### Je n'arrive pas a accéder à l'interface via une url \*.local

L'interface sur un poste développeur doit-être accessible via les URLs:

- http://quefairedemesdechets.ademe.local/
- http://quefairedemesobjets.ademe.local/
- http://lvao.ademe.local/ : redirigé vers le site institutionnel

Si tel n'est pas le cas, voici quelques configuration à vérifier

#### /etc/hosts

Dans la configuration `/etc/hosts`, vérifier la présence des lignes

```
127.0.0.1       lvao.ademe.local
127.0.0.1       quefairedemesdechets.ademe.local
127.0.0.1       quefairedemesobjets.ademe.local
```

#### Vérifier la présence des certificats ssl

Si les certificats ne sont pas présents, les logs du serveur nginx affichent une erreur type

```
lvao-proxy-1  | 2025/05/20 10:47:25 [emerg] 1#1: cannot load certificate "/etc/nginx/ssl/lvao.ademe.local+1.pem": BIO_new_file() failed (SSL: error:80000002:system library::No such file or directory:calling fopen(/etc/nginx/ssl/lvao.ademe.local+1.pem, r) error:10000080:BIO routines::no such file)
```

Dans ce cas, (re-)générer les certificats

```
make init-certs
```

#### .env

Enfin, vérifier les variables d'environnement en prenant exemple sur le fichier `.env.template`

## Stack data, airflow, dbt

En local, il peut s'avérer complexe de développer sur la stack data, du fait du volume de données, mais aussi de l'enchaînement de tâches dans les DAGs.

### Visualiser les logs d'un DAG en échec

Si un dag échoue, il peut être utile de visualiser ses logs.
Pour ce faire,

1. cliquer sur la tâche échouée (`failed`)
2. cliquer dans l'onglet `Logs`
3. cliquer sur `see more`
   ![./_medias/troubleshooting-1.png]()

Cela va amener à une vue détaillée des logs du DAG échuoée

### Rejouer une tâche `dbt` d'un DAG

DBT est utilisé pour transformer les données en base de données.
En visualisant les logs d'une tâche en échec, on peut retrouver la commande `dbt` utilisée pour executer cette tâche. En général cela se situe tout en haut des logs

```
[2025-07-09, 06:53:26 UTC] {local_task_job_runner.py:123} ▶ Pre task execution logs
[2025-07-09, 06:53:26 UTC] {subprocess.py:78} INFO - Tmp dir root location: /tmp
[2025-07-09, 06:53:26 UTC] {subprocess.py:88} INFO - Running command: ['/usr/bin/bash', '-c', 'dbt run --models intermediate.acteurs']
[2025-07-09, 06:53:26 UTC] {subprocess.py:99} INFO - Output:
[2025-07-09, 06:53:28 UTC] {subprocess.py:106} INFO - 06:53:28  Running with dbt=1.10.2
```

Ici, `dbt run --models intermediate.acteurs`

En supposant que vous avez une stack airflow en local, vous pouvez recopier cette commande dans le conteneur `airflow-scheduler` :

```sh
# depuis la racine du repo, où le fichier docker-compose.yml se situe
docker compose exec airflow-scheduler dbt run --models intermediate.acteurs
```

Ainsi, vous pouvez désormais effectuer toutes les modifications de code souhaitées dans vos modèles avant de rejouer cette tâche.

## Créer un utilisateur sur Airflow sans accès à la UI

Il est possible de créer un user directement depuis `psql`, pour ce faire

1. Générer un mot de passe en utilisant `werkzeug` utilisé par Airflow

```py
# Depuis un shell python, par exemple uv run python
from werkzeug.security import generate_password_hash

print(generate_password_hash('your_password'))
# Retourne une string ressemblant à pbkdf2:sha256:260000$abc123$...
```

2. Insérer le nouvel utilisateur dans la table `ab_user`

Récupérer la commande de connexion depuis le dashboard Scaleway (dans notre cas):

```sh
psql -h databae_host_name -p 5432 -U user -d airflow_database`
```

Executer le `SQL` ci-dessous

```sql
INSERT INTO ab_user (
    id, first_name, last_name, username, password, email, active
) VALUES (
    1000, 'Admin', 'User', 'admin', 'pbkdf2:sha256:260000$abc123$...', 'admin@example.com', true
);
```

À noter : assurez vous que 1000 n'est pas déjà utilisé. Il est possible de récupérer l'ID le plus haut avec la commande

```sql
SELECT MAX(id) FROM ab_user;
```

3. Assigner le rôle `Admin`

Commencez par trouver l'ID du rôle `Admin`

```sql
SELECT id FROM ab_role WHERE name = 'Admin';
```

En supposant que l'ID soit `1`, l'insérer dans la table de lien

```sql
INSERT INTO ab_user_role (user_id, role_id) VALUES (1000, 1);
```

BONUS : avec un accès au CLI Airflow, c'est quand même beaucoup plus simple :

```sh
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password your_password
```

Malheureusement on a pas d'accès shell actuellement sur nos instances déployées dans Scaleway...

## Inspecter une image docker

Si une image docker ne démarre pas, par exemple si elle ne trouve pas ses librairies. il est possible de la construire et de la parcourrir avec les commandes suivantes:

Build:

```sh
docker build --no-cache -f airflow-webserver.Dockerfile -t airflow-webserver .
```

Executer un shell sur l'image:

```sh
docker run --rm -it --user root --entrypoint /bin/bash airflow-webserver
```

Par exemple, nous avons eu un problème `airflow.providers.amazon Module not found` que nous avons investiguer de la manière suivante :

```sh
$> docker run --rm -it --user root --entrypoint /bin/bash airflow-webserver
root@1274bcd93c28:/opt/airflow# python
Python 3.12.12 (main, Nov 14 2025, 13:51:59) [GCC 12.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import airflow.providers.amazon
…
```

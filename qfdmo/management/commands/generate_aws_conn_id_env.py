import os

from airflow.models.connection import Connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Génère une connexion AWS pour Airflow et affiche l'URI de connexion"

    def add_arguments(self, parser):

        parser.add_argument(
            "--access_key",
            type=str,
            help="Clé d'accès AWS (login)",
            required=True,
        )
        parser.add_argument(
            "--secret_key",
            type=str,
            help="Clé secrète AWS (password)",
            required=True,
        )
        parser.add_argument(
            "--conn_id",
            type=str,
            default="log_default",
            help="ID de la connexion Airflow (défaut: 'log_default')",
        )
        parser.add_argument(
            "--bucket_name",
            type=str,
            default="qfdmo-airflow-logs",
            help="Nom du bucket S3 (défaut: 'qfdmo-airflow-logs')",
        )

    def handle(self, *args, **options):
        access_key = options["access_key"]
        secret_key = options["secret_key"]
        conn_id = options["conn_id"]
        bucket_name = options["bucket_name"]
        if not bucket_name.startswith("s3://"):
            bucket_name = f"s3://{bucket_name}"

        extra = {
            "region": "fr-par",
            "endpoint_url": "https://s3.fr-par.scw.cloud",
            "port": 443,
            # "use_ssl": True,
            # "verify": False,
        }

        conn = Connection(
            conn_id=conn_id,
            conn_type="aws",
            login=access_key,
            password=secret_key,
            extra=extra,
        )

        # Generate Environment Variable Name and Connection URI
        env_key = f"AIRFLOW_CONN_{conn.conn_id.upper()}"
        conn_uri = conn.get_uri()

        os.environ[env_key] = conn_uri

        # Display output
        self.stdout.write(
            self.style.WARNING("Ajoutez la variable d'environnement suivante:\n")
        )
        self.stdout.write('AIRFLOW__LOGGING__REMOTE_LOGGING="true"\n')
        self.stdout.write(f'AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER="{bucket_name}"\n')
        self.stdout.write(f'AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID="{conn_id}"\n')
        self.stdout.write('AIRFLOW__LOGGING__ENCRYPT_S3_LOGS="false"\n')
        self.stdout.write(f'{env_key}="{conn_uri}"\n')

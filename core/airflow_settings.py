from core.settings import *  # noqa: F403

# Inactive the logging when Django is use in Airflow because it's not compatible
# with the Airflow logging system when saving logs to s3 storage
LOGGING_CONFIG = None

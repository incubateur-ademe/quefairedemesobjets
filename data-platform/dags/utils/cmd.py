"""Utilities to run system commands in Airflow. It shouldn't replace
BashOperator if we can make simple use of that operator, however in
pipelines such as the replication of Annuaire Enterprise where we
need to issue variable commands inside Python logic we found it
was useful to have"""

import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cmd_run(cmd: str, dry_run: bool = True, env: dict = {}) -> str | None:
    """Runs a system command with optional dry-run mode,
    Useful to run low-level tasks (e.g. streaming a remove CSV
    into DB via psql) while keeping the logic in Python."""
    logger.info("")  # space out commands if several in a row
    logger.info("💻 Lancement de la commande...")
    if dry_run:
        logger.info(f"💻 commande: {dry_run=}, pas executée")
        return None

    logger.info("💻 commande: éxecution commencée 🔵")
    process = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
        # Passing passwords via env so they don't show in airflow logs
        # e.g. when using psql use env={"PGPASSWORD": pwd},
        env=env,
    )
    # Error
    if process.returncode != 0 or process.stderr:
        raise SystemError(f"💻 commande: erreur 🔴 {process.stderr}")

    # Everything went OK
    logger.info(f"💻 commande: résultat={process.stdout}")
    logger.info("💻 commande: éxecution terminée 🟢")
    return process.stdout

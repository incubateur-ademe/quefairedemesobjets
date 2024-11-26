import importlib
import logging
from itertools import chain

from sources.tasks.airflow_logic.config_management import get_nested_config_parameter
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_config_validate(
    params: dict,
    codes_sc_db: set[str],
) -> None:
    """Etape de validation des paramètres de configuration du DAG
    pour éviter d'engendrer des coûts d'infra (et de fournisseurs API)
    si on peut déjà déterminer que le DAG ne pourra pas fonctionner
    """
    # TODO: la validation de la structure même des paramètres devrait
    # se faire avec un schéma de validation (dataclass, pydantic, etc.)
    # potentiellement appliqué directement dans le fichier DAG

    # Validation des sous-catégories produit qui doivent être mappées
    # et toutes correspondre à des codes valides dans notre DB
    logger.info("Validation sous-catégories produit: début...")
    product_mapping = params.get("product_mapping", {})
    if not product_mapping:
        raise ValueError("product_mapping manquant pour la source")
    # Le mapping est 1->N, donc on doit écraser pour avoir une liste aplatie
    codes_sc_params = set(
        chain.from_iterable(
            (x if isinstance(x, list) else [x]) for x in product_mapping.values()
        )
    )
    codes_sc_invalid = codes_sc_params - codes_sc_db
    log.preview("Codes sous-cat dans params", codes_sc_params)
    log.preview("Codes sous-cat dans DB", codes_sc_db)

    if codes_sc_invalid:
        raise ValueError(f"Codes product_mapping invalides: {codes_sc_invalid}")
    logger.info("Validation sous-catégories produit: ✅ succès.")

    column_mapping = params.get("column_mapping", {})
    if not isinstance(column_mapping, dict):
        raise ValueError("column_mapping doit être un dictionnaire")

    column_transformations = params.get("column_transformations", [])
    column_transformations = get_nested_config_parameter(column_transformations)
    if not isinstance(column_transformations, list):
        raise ValueError("column_transformations doit être une liste")

    # Tester si les fonctions existent
    function_names = [x["transformation"] for x in column_transformations]
    for function_name in function_names:
        module_name = "sources.tasks.transform"
        module = importlib.import_module(module_name)
        try:
            function_callable = getattr(module, function_name)
        except AttributeError:
            raise ValueError(
                f"La fonction de transformation {function_name} n'existe pas dans"
                f" {module_name}"
            )
        if not callable(function_callable):
            raise ValueError(
                f"La fonction de transformation {function_callable} n'est pas callable"
            )

    # La validation de config ne doit pas changer les données, donc
    # on retourne explicitement None
    return None

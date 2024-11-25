import logging
from itertools import chain

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
        logger.warning(f"Codes sous-cat DB non trouvés dans params: {codes_sc_invalid}")
        # raise ValueError(f"Codes product_mapping invalides: {codes_sc_invalid}")
    logger.info("Validation sous-catégories produit: ✅ succès.")

    # La validation de config ne doit pas changer les données, donc
    # on retourne explicitement None
    return None

"""
Test de la fonction parent_get_data_from_acteurs qui permet de fusionner
les données de plusieurs acteurs pour en faire un parent, en priorisant
les sources de préférence puis les données les plus complètes.
"""

from qfdmo.models import RevisionActeur
from scripts.deduplication.tasks.db_manage_parent import parent_get_data_from_acteurs


def test_parent_get_data_from_acteurs():
    acteurs = [
        {
            "identifiant_externe": "A",
            "identifiant_unique": "a",
            "nom": "Mon A",
            "url": "url_a",
            "siren": None,
            "source_id": 1,
            "parent_id": None,
        },
        {
            "identifiant_externe": "B",
            "identifiant_unique": "b",
            "nom": "Mon B",
            "url": None,
            "siret": 12345678912345,
            "source_id": 2,
            "parent_id": "p1",
        },
        {
            "identifiant_externe": "C",
            "identifiant_unique": "c",
            "nom": "Mon C",
            "url": None,
            "siret": None,
            "source_id": 3,
            "parent_id": "p2",
            "email": "INVALID",
        },
        {
            "identifiant_externe": "D",
            "identifiant_unique": "d",
            "nom": "Mon D",
            "url": None,
            "siret": None,
            "source_id": 4,
            "parent_id": "p2",
            "email": "INVALID",
        },
    ]
    source_ids_preferred = [3, 2]
    parent_expected = {
        # Intentionnellement pas de identifiant_unique retourné
        # pour nous forcer à gérer le ID séparément (ex: génréer un UUID)
        "nom": "Mon C",
        "url": "url_a",
        "siret": 12345678912345,
        "source_id": None,
    }
    parent = parent_get_data_from_acteurs(acteurs, source_ids_preferred, RevisionActeur)  # type: ignore
    assert parent == parent_expected

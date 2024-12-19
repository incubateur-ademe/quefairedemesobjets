""""
Test de la fonction parent_get_data_from_acteurs qui permet de fusionner
les données de plusieurs acteurs pour en faire un parent, en priorisant
les sources de préférence puis les données les plus complètes.


Cas de figures à tester:
 - un champ n'est jamais rempli si toutes les valeurs dispos sont None
 - le source_id est mis à None pour expliciter la non-source (càd parent fabriqué)
 - les autres id (identifiant, parent_id) ne doivent pas être remplis
 - location: on priorise une source autre que les sources par défaut
 - email: on ne prend pas de mauvais email
"""

import pytest
from django.contrib.gis.geos import Point

from qfdmo.models import RevisionActeur
from scripts.deduplication.tasks.db_manage_parent import parent_get_data_from_acteurs

# Pour l'instant notre code a été conçu pour les déchetteries
ACTEUR_TYPE_ID = 7

SOURCE_IDS_BY_CODES = {
    # A noter le code REFASHION tel que
    # présent dans la base (son id peut différé)
    # parce que la règle de résolution des champs
    # est pour l'instant en dure dans
    "REFASHION": 123456789,
    "ALIAPUR": 456,
    "COREPILE": 46511111,
    "Bon url": 654,
    "Bon email & siret": 789,
    "Bon nom": 111,
}
SOURCES_PREFERRED_IDS = [
    SOURCE_IDS_BY_CODES["Bon nom"],
    SOURCE_IDS_BY_CODES["Bon url"],
]
SOURCE_CODES_PICKED_EXPECTED = {
    "nom": "COREPILE",
    "url": "Bon url",
    "location": "REFASHION",
    "siret": "Bon email & siret",
    "email": "Bon email & siret",
    # C'est la première source qui a été choisie
    # pour l'acteur type
    "acteur_type_id": "Bon url",
}
PARENT_EXPECTED = {
    # Intentionnellement pas de identifiant_unique retourné
    # pour nous forcer à gérer le ID séparément (ex: génréer un UUID)
    "nom": "nom de COREPILE",
    "url": "url_a",
    "siret": 11111111111111,
    "location": Point(1, 2),
    # Le source_id est nulle parce que le parent est généré par nous
    # donc ne provient d'aucune source en particulier
    "source_id": None,
    "acteur_type_id": ACTEUR_TYPE_ID,
}


class TestParentDataFromActeur:

    @pytest.fixture(scope="session")
    def acteurs_get(self) -> list[dict]:
        return [
            {
                "identifiant_externe": "A",
                "identifiant_unique": "a",
                "adresse_complement": None,
                "nom": "Mon A",
                "url": "url_a",
                "siren": None,
                "source_id": SOURCE_IDS_BY_CODES["Bon url"],
                "parent_id": None,
                "acteur_type_id": ACTEUR_TYPE_ID,
                "cree_le": "2021-01-01",
                "modifie_le": "2021-01-01",
            },
            {
                "identifiant_externe": "B",
                "identifiant_unique": "b",
                "adresse_complement": None,
                "nom": "Mon B",
                "url": None,
                "siret": 12345678912345,
                "siren": 123456789,
                "telephone": "02 43 56 78 90",
                "source_id": SOURCE_IDS_BY_CODES["REFASHION"],
                "parent_id": "p1",
                "location": Point(1, 2),
                "acteur_type_id": ACTEUR_TYPE_ID,
            },
            {
                "identifiant_externe": "C",
                "identifiant_unique": "c",
                "nom": "nom de COREPILE",
                "url": None,
                "siret": None,
                "source_id": SOURCE_IDS_BY_CODES["COREPILE"],
                "parent_id": "p2",
                "email": "INVALID",
                # location non-nulle sur la source id préférée (3)
                # mais qui sera ignorée car source 45 (REFASHION)
                # est prioritaire sur les locations
                "location": Point(0, 0),
                "acteur_type_id": ACTEUR_TYPE_ID,
            },
            {
                "identifiant_externe": "D",
                "identifiant_unique": "d",
                "nom": "Mon D",
                "url": None,
                "siret": 11111111111111,
                "source_id": SOURCE_IDS_BY_CODES["Bon email & siret"],
                "parent_id": "p2",
                # on met le bon email sur une location
                "email": "correct@example.org",
                "acteur_type_id": ACTEUR_TYPE_ID,
            },
        ]

    @pytest.fixture(scope="session")
    def results_get(self, acteurs_get) -> tuple[dict, dict]:

        return parent_get_data_from_acteurs(
            acteurs=acteurs_get,
            source_ids_by_code=SOURCE_IDS_BY_CODES,
            sources_preferred_ids=SOURCES_PREFERRED_IDS,
            validation_model=RevisionActeur,  # type: ignore
        )

    @pytest.fixture(scope="session")
    def parent(self, results_get) -> dict:
        parent, _ = results_get
        return parent

    @pytest.fixture(scope="session")
    def source_codes_picked(self, results_get) -> dict:
        _, source_codes_picked = results_get
        return source_codes_picked

    def test_field_never_filled_because_all_none(self, parent):
        """On ne remplit pas un champs si toutes les valeurs dispos sont None"""
        assert "adresse_complement" not in parent

    def test_datetimes_are_removed(self, parent):
        """Les dates de création et modification ne sont pas copiées"""
        assert "cree_le" not in parent
        assert "modifie_le" not in parent

    def test_source_id_set_to_none(self, parent):
        """Pour expliciter que le parent a été fabriqué par nous"""
        assert parent["source_id"] is None

    def test_acteur_type_id_remains_same(self, parent):
        """L'acteur type est conservé"""
        assert parent["acteur_type_id"] == ACTEUR_TYPE_ID

    def test_ids_not_present_except_source_id(self, parent):
        """On ne renseigne pas les autres ids, qui seront
        assignés plus tard (id parent existant ou UUID pour nouveau)"""
        assert "parent_id" not in parent
        assert "identifiant_unique" not in parent

    def test_email_picked_is_valid(self, parent):
        """On a réussi à exclure le mauvais email"""
        assert parent["email"] == "correct@example.org"

    def test_field_mapping_source_picked_preferred(self, source_codes_picked):
        """Pour le location, on a réussi à avoir la source qui était
        n1 pour ce champ"""
        assert source_codes_picked["location"] == "REFASHION"

    def test_field_mapping_source_picked_fallback(self, source_codes_picked):
        """Pour le nom, on avait la source préférée, mais a réussi notre fallback
        sur la 2ème"""
        assert source_codes_picked["nom"] == "COREPILE"

    def test_field_mapping_source_exclusions(self, source_codes_picked):
        """Pour plusieurs champs, on a réussi à exclure la source qui avait un siret
        non-nul mais invalide"""
        assert source_codes_picked["siret"] != "REFASHION"
        assert source_codes_picked["siret"] == "Bon email & siret"

        assert "siren" not in source_codes_picked
        assert "telephone" not in source_codes_picked

    def test_source_ids_picked(self, results_get):
        """Vérification d'ensemble sur les sources choisies pour
        s'assurer qu'il n'y a pas des champs définis dans
        SOURCE_CODES_PICKED_EXPECTED qui sont passés aux oubliettes"""
        _, source_codes_picked = results_get
        assert source_codes_picked == SOURCE_CODES_PICKED_EXPECTED

    def test_parent_dict(self, parent):
        # On ne peut pas comparer les dicts
        # en entier directement à cause de "location"
        # dont le hash est une ref mémoire, et donc non-deterministe
        # Point(1, 2) <=> Point(1, 2)
        # {'location': <Point object at 0x7162a95f0a20>} <=>
        # {'location': <Point object at 0x7162a95f0e20>}
        for key in PARENT_EXPECTED:
            if key == "location":
                assert parent[key].coords == PARENT_EXPECTED[key].coords
            else:
                assert parent[key] == PARENT_EXPECTED[key]

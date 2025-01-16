"""
Fichier de tests dédiés aux propriétés calculées/dérivées de l'acteur
(@property, @cached_property).

TODO: déplacés les tests de test_acteur.py vers ce fichier concernant les
propriétés pour avoir une vue d'ensemble ici.

"""

import pytest

from qfdmo.models import Acteur


class TestActeurProperties:

    @pytest.mark.parametrize(
        "input,expected",
        [
            # Les cas de base
            ("32 rue Léon Gautier", "32"),
            ("15 b avenur des moulins", "15 b"),
            ("1 bis esplanade de la mer", "1 b"),
            ("1 boulevard de la liberté", "1"),
            ("45c rue de la paix", "45 c"),
            # Les cas où l'adresse n'est pas propre
            # et ne commence pas exactement par le numéro
            ("      1 bis esplanade de la mer", "1 b"),
            # Si il y a plusieurs numéros, pour l'instant
            # on prend le premier
            ("14-16 rue des moulins", "14"),
            # Normalisation (minuscule + séparation num./compl.)
            # et bis en b
            (" 15 BIS  rue des moulins", "15 b"),
            (" 15bis  ", "15 b"),
            # Les cas où on ne doit pas obtenir de numéro
            # car il ne se situe pas au début de l'adresse
            ("Place du 14 juillet", None),
            # Les cas où l'adresse est vide
            ("", None),
            (None, None),
        ],
    )
    def test_numero_et_complement_de_rue(self, input, expected):
        acteur = Acteur(adresse=input)
        assert acteur.numero_et_complement_de_rue == expected

    @pytest.mark.parametrize(
        "input,expected",
        [
            # CP à 5 chiffre avec 0 au début
            ("01234", "01"),
            (" 01234 ", "01"),
            # CP à 5 chiffre sans 0 au début
            ("75000", "75"),
            (" 75000 ", "75"),
            # CP qu'on considère invalides
            ("123456", None),
            # On pourrait tenter le 4 chiffres
            # mais c'est mieux de laisser au champ
            # code_postal le soin de faire sa validation
            ("1234", None),
            ("  ", None),
            ("", None),
            (None, None),
        ],
    )
    def test_code_departement(self, input, expected):
        acteur = Acteur(code_postal=input)
        assert acteur.code_departement == expected

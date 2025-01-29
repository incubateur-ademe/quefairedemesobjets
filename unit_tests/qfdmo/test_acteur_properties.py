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

    @pytest.mark.parametrize(
        "adresse,adresse_complement,expected",
        [
            # Les cas remplis complètement
            ("  a ", "  b  ", "a b"),
            ("  foo   bar ", "  b  ", "foo   bar b"),
            # Les cas remplis partièllement
            ("  foo   bar ", None, "foo   bar"),
            ("", " a b c ", "a b c"),
            # Les cas vides
            (None, None, None),
            (None, "  ", None),
            ("   ", None, None),
            ("   ", "     ", None),
        ],
    )
    def test_combine_adresses(self, adresse, adresse_complement, expected):
        acteur = Acteur(adresse=adresse, adresse_complement=adresse_complement)
        assert acteur.combine_adresses == expected

    @pytest.mark.parametrize(
        "nom,nom_commercial,nom_officiel,expected",
        [
            # Les cas remplis complètement
            ("  a ", "  b  ", "  c  ", "a b c"),
            ("  foo   bar ", "  b  ", "  c  ", "foo   bar b c"),
            # Les cas remplis partièllement
            ("  foo   bar ", None, "  c  ", "foo   bar  c"),
            ("", " a b c ", "  c  ", "a b c c"),
            # Les cas vides
            (None, None, None, None),
            (None, "  ", None, None),
            ("   ", None, None, None),
            ("   ", "     ", None, None),
            ("   ", "     ", "     ", None),
        ],
    )
    def test_combine_noms(self, nom, nom_commercial, nom_officiel, expected):
        acteur = Acteur(
            nom=nom,
            nom_commercial=nom_commercial,
            nom_officiel=nom_officiel,
        )
        assert acteur.combine_noms == expected

    @pytest.mark.parametrize(
        "nom,ville,expected",
        [
            # Les cas remplis complètement
            # ville supprimée
            ("  DECATHLON Clermond-Ferrand ", " CLéRMOND FErrAND", "DECATHLON"),
            (" éclairage Lâvâl ", "  LAVAL ", "éclairage"),
            # ville non supprimée
            ("  Decathlon Laval ", "  CHALLANS  ", "Decathlon Laval"),
            # Les cas remplis partièllement
            ("  foo   bar ", None, "foo bar"),
            (" mon acteur ", " a b c ", "mon acteur"),
            # Les cas vides
            (None, None, None),
            (None, "  ", None),
            ("   ", None, None),
            ("   ", "     ", None),
        ],
    )
    def test_nom_sans_ville(self, nom, ville, expected):
        acteur = Acteur(nom=nom, ville=ville)
        assert acteur.nom_sans_ville == expected

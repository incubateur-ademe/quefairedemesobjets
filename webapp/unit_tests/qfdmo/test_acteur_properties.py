"""
Fichier de tests dédiés aux propriétés calculées/dérivées de l'acteur
(@property, @cached_property).

TODO: déplacés les tests de test_acteur.py vers ce fichier concernant les
propriétés pour avoir une vue d'ensemble ici.

"""

import pytest

from qfdmo.models import Acteur
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    RevisionActeurFactory,
)


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
        "nom,adresse,adresse_complement,expected",
        [
            # Les cas remplis complètement
            ("  à B C ", "  b  ", "  c  ", "à"),
            (
                "Décathlon rue des étangs za Rocher",
                "RUE DES ETANGS",
                " ZA rocher ",
                "Décathlon",
            ),
        ],
    )
    def test_nom_sans_combine_adresses(
        self, nom, adresse, adresse_complement, expected
    ):
        acteur = Acteur(nom=nom, adresse=adresse, adresse_complement=adresse_complement)
        assert acteur.nom_sans_combine_adresses == expected

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


class TestParentsCache:

    @pytest.mark.django_db
    def test_nombre_enfants_revision_and_diplayed(self):
        # p1 = acteur parent avec 3 enfants, on démontre que la propriété
        # calculée nombre_enfants fonctionne au niveau revision et displayed
        r1 = RevisionActeurFactory(identifiant_unique="p1")
        d1 = DisplayedActeurFactory(identifiant_unique="p1")
        a = RevisionActeurFactory(identifiant_unique="a_r1", parent=r1)
        b = RevisionActeurFactory(identifiant_unique="b_r1", parent=r1)
        c = RevisionActeurFactory(identifiant_unique="c_r1", parent=r1)

        # r2 = acteur non parent donc avec 0 enfants
        r2 = RevisionActeurFactory(identifiant_unique="r2_pas_parent")

        assert r1.nombre_enfants == 3
        assert d1.nombre_enfants == 3
        assert r2.nombre_enfants == 0

        # On supprime un enfant et on démontre l'invalidation du cache
        a.parent = r2  # p1--, r2++
        a.save()
        assert r1.nombre_enfants == 2
        assert d1.nombre_enfants == 2
        assert r2.nombre_enfants == 1

        b.parent = None  # p1--, r2=
        b.save()
        assert r1.nombre_enfants == 1
        assert d1.nombre_enfants == 1
        assert r2.nombre_enfants == 1

        c.parent = r2  # p1--, r2++
        c.save()
        assert r1.nombre_enfants == 0
        assert d1.nombre_enfants == 0
        assert r2.nombre_enfants == 2

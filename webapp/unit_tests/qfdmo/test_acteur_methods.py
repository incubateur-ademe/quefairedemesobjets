"""Test file dedicated to acteur methods"""

import json

import pytest

from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
)


@pytest.mark.django_db
class TestActeurMethods:

    @pytest.mark.parametrize(
        "initial,expected",
        [
            ("", [{"message": "test"}]),
            ("  ", [{"message": "test"}]),
            ("foo", [{"message": "foo"}, {"message": "test"}]),
            ('[{"message": "bar"}]', [{"message": "bar"}, {"message": "test"}]),
        ],
    )
    def test_commentaires_ajouter(self, initial, expected):
        acteur = ActeurFactory(commentaires=initial)
        acteur.commentaires_ajouter("test")
        actual = json.loads(acteur.commentaires)
        assert actual == expected

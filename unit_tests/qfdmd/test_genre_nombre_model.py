import pytest

from qfdmd.models import GenreNombreModel


@pytest.fixture(scope="module")
def concrete_model():
    # Create a concrete model for testing the abstract GenreNombreModel
    class ConcreteGenreNombreModel(GenreNombreModel):
        class Meta:
            app_label = "test"

    return ConcreteGenreNombreModel


def test_pronom_returns_mes_for_pluriel(concrete_model):
    instance = concrete_model(
        genre=GenreNombreModel.Genre.MASCULIN, nombre=GenreNombreModel.Nombre.PLURIEL
    )
    assert (
        instance.pronom == "mes"
    ), "Test that pronom returns 'mes' for plural forms regardless of gender"

    instance = concrete_model(
        genre=GenreNombreModel.Genre.FEMININ, nombre=GenreNombreModel.Nombre.PLURIEL
    )
    assert (
        instance.pronom == "mes"
    ), "Test that pronom returns 'mes' for plural forms regardless of gender"


def test_pronom_returns_ma_for_feminin_singulier(concrete_model):
    instance = concrete_model(
        genre=GenreNombreModel.Genre.FEMININ, nombre=GenreNombreModel.Nombre.SINGULIER
    )
    assert (
        instance.pronom == "ma"
    ), "Test that pronom returns 'ma' for feminine singular"


def test_pronom_returns_mon_for_masculin_singulier(concrete_model):
    instance = concrete_model(
        genre=GenreNombreModel.Genre.MASCULIN, nombre=GenreNombreModel.Nombre.SINGULIER
    )
    assert (
        instance.pronom == "mon"
    ), "Test that pronom returns 'mon' for masculine singular"


def test_pronom_returns_mon_for_empty_genre_singulier(concrete_model):
    instance = concrete_model(genre="", nombre=GenreNombreModel.Nombre.SINGULIER)
    assert (
        instance.pronom == "mon"
    ), "Test that pronom returns 'mon' when genre is empty and number is singular"


def test_pronom_returns_mon_for_null_nombre(concrete_model):
    instance = concrete_model(genre=GenreNombreModel.Genre.MASCULIN, nombre=None)
    assert (
        instance.pronom == "mon"
    ), "Test that pronom returns 'mon' when nombre is null (default case)"

    instance = concrete_model(genre=GenreNombreModel.Genre.FEMININ, nombre=None)
    assert (
        instance.pronom == "ma"
    ), "Test that pronom returns 'ma' for feminine when nombre is null"


def test_pronom_returns_mon_for_empty_fields(concrete_model):
    instance = concrete_model(genre="", nombre=None)
    assert (
        instance.pronom == "mon"
    ), "Test that pronom returns 'mon' when both fields are empty/null"

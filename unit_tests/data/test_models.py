import pytest

from data.models import (  # Remplacez YourModel par le nom de votre modèle
    SuggestionAction,
    SuggestionCohorte,
)


@pytest.mark.parametrize(
    "type_action, expected_result",
    [
        (SuggestionAction.SOURCE_AJOUT, True),
        (SuggestionAction.SOURCE_MISESAJOUR, True),
        (SuggestionAction.SOURCE_SUPPRESSION, True),
        (SuggestionAction.CLUSTERING, False),
        ("other_action", False),
    ],
)
def test_is_source_type(type_action, expected_result):
    instance = SuggestionCohorte(type_action=type_action)
    assert instance.is_source_type == expected_result


@pytest.mark.parametrize(
    "type_action, expected_result",
    [
        (SuggestionAction.CLUSTERING, True),
        (SuggestionAction.SOURCE_AJOUT, False),
        (SuggestionAction.SOURCE_MISESAJOUR, False),
        (SuggestionAction.SOURCE_SUPPRESSION, False),
        ("other_action", False),
    ],
)
def test_is_clustering_type(type_action, expected_result):
    instance = SuggestionCohorte(type_action=type_action)
    assert instance.is_clustering_type == expected_result

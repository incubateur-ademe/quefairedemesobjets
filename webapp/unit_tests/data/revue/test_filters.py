import pytest
from data.models.suggestion import SuggestionAction, SuggestionCohorte
from data.revue.cohortes import COHORTE_FIELDS
from data.revue.errors import RevueApiError
from data.revue.filters import (
    MAX_CONDITIONS,
    apply_filter,
    parse_filter,
    registry_metadata,
)
from unit_tests.data.models.suggestion_factory import SuggestionCohorteFactory


def cond(field, operator, value=None):
    return {"field": field, "operator": operator, "value": value}


def tree(*conditions, op="and"):
    return {"op": op, "conditions": list(conditions)}


def ids(filtre):
    queryset = apply_filter(SuggestionCohorte.objects.all(), filtre, COHORTE_FIELDS)
    return set(queryset.values_list("identifiant_action", flat=True))


@pytest.fixture
def cohortes():
    SuggestionCohorteFactory(
        identifiant_action="Écosystème_DAG",
        type_action=SuggestionAction.SOURCE_AJOUT,
        metadata={"source_code": "ecomaison", "nb": 3},
    )
    SuggestionCohorteFactory(
        identifiant_action="refashion_dag",
        type_action=SuggestionAction.SOURCE_MODIFICATION,
        metadata={"source_code": "Refashion"},
    )
    SuggestionCohorteFactory(
        identifiant_action="",
        type_action=SuggestionAction.SOURCE_SUPPRESSION,
        metadata=None,
    )


@pytest.mark.django_db
class TestTextOperators:
    def test_comparisons_ignore_case_and_accents(self, cohortes):
        assert ids(tree(cond("identifiant_action", "eq", "ecosysteme_dag"))) == {
            "Écosystème_DAG"
        }
        assert ids(tree(cond("identifiant_action", "icontains", "SYSTEME"))) == {
            "Écosystème_DAG"
        }
        assert ids(tree(cond("identifiant_action", "startswith", "REF"))) == {
            "refashion_dag"
        }

    def test_in_and_neq(self, cohortes):
        assert ids(
            tree(cond("identifiant_action", "in", ["ECOSYSTEME_dag", "refashion_DAG"]))
        ) == {"Écosystème_DAG", "refashion_dag"}
        assert ids(tree(cond("identifiant_action", "neq", "refashion_dag"))) == {
            "Écosystème_DAG",
            "",
        }

    def test_empty(self, cohortes):
        assert ids(tree(cond("identifiant_action", "is_empty"))) == {""}
        assert ids(tree(cond("identifiant_action", "is_not_empty"))) == {
            "Écosystème_DAG",
            "refashion_dag",
        }

    def test_json_key(self, cohortes):
        assert ids(tree(cond("metadata.source_code", "eq", "refashion"))) == {
            "refashion_dag"
        }
        assert ids(tree(cond("metadata.source_code", "is_empty"))) == {""}


@pytest.mark.django_db
class TestOtherTypes:
    def test_choice(self, cohortes):
        assert ids(
            tree(cond("type_action", "in", ["SOURCE_AJOUT", "SOURCE_SUPRESSION"]))
        ) == {"Écosystème_DAG", ""}

    def test_number_between(self, cohortes):
        first = SuggestionCohorte.objects.order_by("id").first()
        assert ids(tree(cond("id", "between", [first.id, first.id]))) == {
            first.identifiant_action
        }

    def test_date(self, cohortes):
        today = SuggestionCohorte.objects.first().cree_le.date().isoformat()
        assert len(ids(tree(cond("cree_le", "eq", today)))) == 3
        assert ids(tree(cond("cree_le", "gt", today))) == set()


@pytest.mark.django_db
class TestTree:
    def test_or_and_nested_groups(self, cohortes):
        filtre = tree(
            cond("type_action", "eq", "SOURCE_AJOUT"),
            tree(
                cond("identifiant_action", "icontains", "refashion"),
                cond("metadata.source_code", "eq", "refashion"),
            ),
            op="or",
        )
        assert ids(filtre) == {"Écosystème_DAG", "refashion_dag"}

    def test_empty_filter_keeps_everything(self, cohortes):
        assert len(ids(None)) == len(ids(tree())) == 3


class TestValidation:
    @pytest.mark.parametrize(
        "filtre,message",
        [
            (tree(cond("inconnu", "eq", "x")), "inconnu"),
            (tree(cond("identifiant_action", "gt", "x")), "Opérateur"),
            (tree(cond("type_action", "eq", "CLUSTERING")), "Valeur inconnue"),
            (tree(cond("id", "eq", "12")), "Nombre"),
            (tree(cond("cree_le", "eq", "12/01/2026")), "Date"),
            (tree(cond("identifiant_action", "in", [])), "liste"),
            (tree(cond("metadata.a__b", "eq", "x")), "inconnu"),
            (tree(tree(tree(tree())), op="and"), "imbriqué"),
            (tree(*[cond("id", "eq", 1)] * (MAX_CONDITIONS + 1)), "Trop"),
            ({"op": "xor", "conditions": []}, "logique"),
        ],
    )
    def test_invalid_filters_are_rejected(self, filtre, message):
        with pytest.raises(RevueApiError, match=message) as error:
            apply_filter(SuggestionCohorte.objects.all(), filtre, COHORTE_FIELDS)
        assert error.value.status == 422

    def test_invalid_json(self):
        with pytest.raises(RevueApiError, match="JSON"):
            parse_filter("{pas du json")


def test_metadata_lists_json_keys():
    champs = registry_metadata(COHORTE_FIELDS, {"metadata": ["source_code"]})
    keys = [champ["key"] for champ in champs]
    assert "metadata.source_code" in keys
    type_action = next(champ for champ in champs if champ["key"] == "type_action")
    assert {choix["value"] for choix in type_action["choix"]} == {
        "SOURCE_AJOUT",
        "SOURCE_MODIFICATION",
        "SOURCE_SUPRESSION",
    }

"""
import pytest
# TODO: activer ce test une fois qu'on sait comment mocker la database
from cluster.tasks.business_logic.cluster_acteurs_db_data_read_acteurs import (
    cluster_acteurs_db_data_read_acteurs,
)


from unit_tests.qfdmo.acteur_factory import (
    ActeurFactory,
    ActeurTypeFactory,
    SourceFactory,
)



@pytest.mark.django_db()
def test_cluster_acteurs_db_data_read_acteurs():

    s1 = SourceFactory(code="source1", libelle="source1")
    atype1 = ActeurTypeFactory(code="type1")
    a1 = ActeurFactory(source=s1, acteur_type=atype1, nom="acteur1", ville="Paris")

    df = cluster_acteurs_db_data_read_acteurs(
        include_source_ids=[1, 2],
        include_acteur_type_ids=[1, 2],
        include_only_if_regex_matches_nom="",
        include_if_all_fields_filled=["nom", "ville"],
        exclude_if_any_field_filled=["siret", "numero_et_complement_de_rue"],
        extra_selection_fields=["ville", "longitude"],
    )
    pass
"""

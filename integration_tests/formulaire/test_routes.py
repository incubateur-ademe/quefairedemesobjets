import pytest


@pytest.mark.django_db
class TestFormulaire:
    def test_common_routes_for_200(self, client):
        """Here are some common routes used in the Formulaire that
        are not always tested and subject to break"""
        for route in [
            # Formulaire home
            "/formulaire",
            # Objet search
            "/qfdmo/get_synonyme_list?q=auray",
            # Formulaire map display
            "/formulaire?map_container_id=formulaire&digital=0&r=387&bounding_box=&direction=jai&action_displayed=preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre&action_list=preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre&sous_categorie_objet=Blu-ray&sc_id=95&adresse=Auray&longitude=-2.990838&latitude=47.668099&preter=on&mettreenlocation=on&reparer=on&donner=on&echanger=on&echanger=on&revendre=on&emprunter=on&louer=on&acheter=on&pas_exclusivite_reparation=on",
            # Formulaire digital acteurs
            "/formulaire?map_container_id=formulaire&digital=1&r=387&bounding_box=&direction=jai&action_displayed=preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre&action_list=preter|emprunter|louer|mettreenlocation|reparer|donner|echanger|acheter|revendre&sous_categorie_objet=Blu-ray&sc_id=95&adresse=Auray&longitude=-2.990838&latitude=47.668099&preter=on&mettreenlocation=on&reparer=on&donner=on&echanger=on&echanger=on&revendre=on&emprunter=on&louer=on&acheter=on&pas_exclusivite_reparation=on",
        ]:
            response = client.get(route)
            assert response.status_code == 200

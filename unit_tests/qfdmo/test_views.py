class TestConfigurateur:
    def test_anonymous_user_cannot_access_configurateur(self, client):
        response = client.get("/iframe/configurateur")
        assert response.status_code == 302
        assert response.url.startswith("/connexion")

    def test_authenticated_user_can_access_configurateur(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="Jean-Michel", password="accedeauconfigurateur"
        )
        client.force_login(user)
        response = client.get("/iframe/configurateur")
        assert response.status_code == 200

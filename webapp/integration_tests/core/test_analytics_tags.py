import pytest


@pytest.mark.django_db
class TestPosthogDataAttributes:
    def test_unauthenticated_request_does_not_render_user_attributes(self, client):
        response = client.get("/carte")
        assert response.status_code == 200
        content = response.content.decode()
        assert "data-analytics-user-username-value" not in content
        assert "data-analytics-user-email-value" not in content

    def test_authenticated_request_renders_user_attributes(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword",  # pragma: allowlist secret
        )
        client.force_login(user)

        response = client.get("/carte")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-analytics-user-username-value="testuser"' in content
        assert 'data-analytics-user-email-value="testuser@example.com"' in content

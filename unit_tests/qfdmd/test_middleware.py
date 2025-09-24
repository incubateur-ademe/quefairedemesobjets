from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from qfdmd.middleware import BetaMiddleware


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def mock_get_response():
    return Mock()


@pytest.fixture
def beta_middleware(mock_get_response):
    return BetaMiddleware(mock_get_response)


@pytest.fixture
def authenticated_user():
    user = Mock(spec=User)
    user.is_authenticated = True
    return user


@pytest.fixture
def anonymous_user():
    user = Mock(spec=AnonymousUser)
    user.is_authenticated = False
    return user


class TestBetaMiddleware:
    @patch("qfdmd.middleware.has_explicit_perm")
    def test_set_beta_mode_from_anonymous_user(
        self, mock_has_explicit_perm, beta_middleware, request_factory, anonymous_user
    ):
        request = request_factory.get("/")
        request.user = anonymous_user

        beta_middleware._set_beta_mode_from(request)

        assert request.beta is False
        mock_has_explicit_perm.assert_not_called()

    @patch("qfdmd.middleware.has_explicit_perm")
    def test_set_beta_mode_from_authenticated_user_without_permission(
        self,
        mock_has_explicit_perm,
        beta_middleware,
        request_factory,
        authenticated_user,
    ):
        mock_has_explicit_perm.return_value = False
        request = request_factory.get("/")
        request.user = authenticated_user

        beta_middleware._set_beta_mode_from(request)

        assert request.beta is False
        mock_has_explicit_perm.assert_called_once_with(
            authenticated_user, "wagtailadmin.can_see_beta_search"
        )

    @patch("qfdmd.middleware.has_explicit_perm")
    def test_set_beta_mode_from_authenticated_user_with_permission(
        self,
        mock_has_explicit_perm,
        beta_middleware,
        request_factory,
        authenticated_user,
    ):
        mock_has_explicit_perm.return_value = True
        request = request_factory.get("/")
        request.user = authenticated_user

        beta_middleware._set_beta_mode_from(request)

        assert request.beta is True
        mock_has_explicit_perm.assert_called_once_with(
            authenticated_user, "wagtailadmin.can_see_beta_search"
        )

    def test_call_sets_beta_and_returns_response(
        self, beta_middleware, request_factory, anonymous_user
    ):
        request = request_factory.get("/")
        request.user = anonymous_user
        expected_response = Mock()
        beta_middleware.get_response.return_value = expected_response

        response = beta_middleware(request)

        assert hasattr(request, "beta")
        assert request.beta is False
        assert response == expected_response
        beta_middleware.get_response.assert_called_once_with(request)

    @patch("qfdmd.middleware.has_explicit_perm")
    def test_call_with_authenticated_user_with_permission(
        self,
        mock_has_explicit_perm,
        beta_middleware,
        request_factory,
        authenticated_user,
    ):
        mock_has_explicit_perm.return_value = True
        request = request_factory.get("/")
        request.user = authenticated_user
        expected_response = Mock()
        beta_middleware.get_response.return_value = expected_response

        response = beta_middleware(request)

        assert request.beta is True
        assert response == expected_response
        beta_middleware.get_response.assert_called_once_with(request)

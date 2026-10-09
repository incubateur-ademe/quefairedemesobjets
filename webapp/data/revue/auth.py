from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import SessionAuth


class SuperuserSessionAuth(SessionAuth):
    """Django session authentication (with CSRF check on unsafe methods) restricted
    to superusers: anonymous → 401, authenticated but not superuser → 403."""

    def authenticate(self, request: HttpRequest, key: str | None):
        user = super().authenticate(request, key)
        if user is None:
            return None
        if not user.is_superuser:
            raise HttpError(403, "Accès réservé aux superutilisateurs")
        return user

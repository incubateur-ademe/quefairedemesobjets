"""API of the SOURCE suggestions review screen, mounted on /api/suggestions/.

Handlers stay thin: business rules live in the other modules of data.revue."""

from django.http import HttpRequest
from ninja import Router

from data.revue.auth import SuperuserSessionAuth
from data.revue.schemas import UserOut

router = Router(auth=SuperuserSessionAuth(), tags=["Revue suggestions"])


@router.get("/me", response=UserOut)
def me(request: HttpRequest):
    return request.auth

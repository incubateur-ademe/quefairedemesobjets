from django.http import HttpRequest, JsonResponse


class RevueApiError(Exception):
    """Error of the review API, rendered as `{code, detail, errors?, current?}`."""

    def __init__(
        self,
        status: int,
        code: str,
        detail: str,
        errors: dict | None = None,
        current: dict | None = None,
    ):
        super().__init__(detail)
        self.status = status
        self.body = {"code": code, "detail": detail}
        if errors is not None:
            self.body["errors"] = errors
        if current is not None:
            self.body["current"] = current


def revue_api_error_handler(request: HttpRequest, exc: RevueApiError) -> JsonResponse:
    return JsonResponse(exc.body, status=exc.status)

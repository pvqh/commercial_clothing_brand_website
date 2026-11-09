from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils import translation

STAFF_PREFIX = "/staff/"


class StaffAreaMiddleware:
    """The staff area is always in Russian and never indexed (contracts/staff-area.md)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.path.startswith(STAFF_PREFIX):
            return self.get_response(request)
        translation.activate("ru")
        request.LANGUAGE_CODE = "ru"
        response = self.get_response(request)
        response["X-Robots-Tag"] = "noindex"
        return response

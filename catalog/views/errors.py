from django.http import HttpRequest, HttpResponseNotFound
from django.template import loader


def not_found(request: HttpRequest, exception: Exception | None = None) -> HttpResponseNotFound:
    """The shopper-facing "not found" page with a way back to the catalog (FR-005)."""
    page = loader.render_to_string("404.html", {"noindex": True}, request=request)
    return HttpResponseNotFound(page)

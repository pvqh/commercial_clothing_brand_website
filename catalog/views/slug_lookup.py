"""Finding a published category or product by its slug in the active language (FR-005, FR-025)."""

from collections.abc import Callable
from typing import Any

from django.db.models import Model
from django.http import Http404, HttpRequest, HttpResponsePermanentRedirect

from .addresses import active_language


def published_by_slug[ModelType: Model](model: type[ModelType], slug: str) -> ModelType | None:
    lookup = {f"slug_{active_language()}": slug, "is_published": True}
    return model._default_manager.filter(**lookup).first()


def redirect_from_old_slug(
    request: HttpRequest, redirect_model: Any, slug: str, path_for: Callable[..., str]
) -> HttpResponsePermanentRedirect:
    """301 to the current address of whatever used `slug` before; 404 when nothing did."""
    language = active_language()
    redirect = redirect_model._default_manager.filter(language=language, old_slug=slug).first()
    if redirect is None:
        raise Http404("No published item has this address.")
    return HttpResponsePermanentRedirect(path_for(redirect.owner, language, current_query(request)))


def current_query(request: HttpRequest) -> str:
    return f"?{request.GET.urlencode()}" if request.GET else ""

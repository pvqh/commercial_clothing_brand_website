from collections.abc import Callable
from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control

SHOPPER_PAGE_MAX_AGE = 60


def public_cache(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Lets browsers and proxies keep successful shopper pages for a minute (FR-024).

    Redirects and errors are left uncached so a fixed address or a newly published page shows
    immediately.
    """

    @wraps(view)
    def cached_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = view(request, *args, **kwargs)
        if response.status_code == 200:
            patch_cache_control(response, public=True, max_age=SHOPPER_PAGE_MAX_AGE)
        return response

    return cached_view
